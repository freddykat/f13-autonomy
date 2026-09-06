from __future__ import annotations

import copy
from dataclasses import fields
from pathlib import Path

from tools.bmw_control_research_matrix import (
    DomainResearchSummary,
    load_manifest,
    summarize_manifest,
    validate_manifest,
)


MANIFEST = Path("validation/manifests/prototype_001_bmw_actuator_research.json")


def test_default_manifest_is_valid_and_non_actuating():
    payload = load_manifest(MANIFEST)

    assert payload["mode"] == "SHADOW_HIL_RESEARCH_ONLY"
    assert payload["live_transmit"] is False
    assert payload["auto_promote"] is False
    assert validate_manifest(payload) == []

    summaries = summarize_manifest(payload)
    assert summaries
    assert all(item.live_actuation_allowed is False for item in summaries)
    assert all(item.tx_allowed is False for item in summaries)


def test_expected_control_domains_exist():
    payload = load_manifest(MANIFEST)
    domains = {item["domain"] for item in payload["domains"]}

    assert {
        "LATERAL_STEERING",
        "LONGITUDINAL",
        "INDICATORS",
        "PARKING_STEERING",
        "PARKING_LONGITUDINAL",
        "GEAR_SELECTION",
        "BRAKE_HOLD",
    }.issubset(domains)


def test_every_domain_requires_feedback_override_and_events():
    payload = load_manifest(MANIFEST)

    for domain in payload["domains"]:
        assert domain["required_feedback"]
        assert domain["driver_override"]
        assert domain["research_events"]


def test_live_tx_enablement_is_rejected():
    payload = load_manifest(MANIFEST)
    payload["live_transmit"] = True

    errors = validate_manifest(payload)

    assert any("live_transmit" in error for error in errors)


def test_domain_tx_enablement_is_rejected():
    payload = load_manifest(MANIFEST)
    payload["domains"][0]["tx_allowed"] = True

    errors = validate_manifest(payload)

    assert any("tx_allowed" in error for error in errors)


def test_low_level_can_or_flexray_command_fields_are_rejected():
    payload = load_manifest(MANIFEST)
    payload["domains"][0]["can_id"] = 0x123
    payload["domains"][1]["slot_id"] = 77

    errors = validate_manifest(payload)

    assert any("forbidden low-level control fields" in error for error in errors)


def test_unreviewed_active_stage_is_rejected():
    payload = load_manifest(MANIFEST)
    payload["domains"][0]["current_stage"] = "ACTIVE"

    errors = validate_manifest(payload)

    assert any("unsupported current_stage" in error for error in errors)


def test_transport_cannot_be_confirmed_pre_validation():
    payload = load_manifest(MANIFEST)
    payload["domains"][0]["transport_confirmed"] = True

    errors = validate_manifest(payload)

    assert any("transport cannot be marked confirmed" in error for error in errors)


def test_hil_design_is_not_ready_while_transport_unconfirmed():
    payload = load_manifest(MANIFEST)
    payload["domains"][0]["current_stage"] = "HIL_ONLY"

    summaries = summarize_manifest(payload)
    lateral = next(item for item in summaries if item.domain == "LATERAL_STEERING")

    assert lateral.ready_for_passive_research is True
    assert lateral.ready_for_hil_design is False


def test_summary_type_has_no_encoder_or_transport_command_fields():
    names = {field.name for field in fields(DomainResearchSummary)}
    forbidden = {
        "can_id",
        "slot_id",
        "frame_id",
        "payload",
        "checksum",
        "alive_counter",
        "sendcan",
        "tx_message",
        "diagnostic_write",
    }

    assert forbidden.isdisjoint(names)
    assert DomainResearchSummary.__dataclass_fields__["status"].default == (
        "CONTROL_RESEARCH_ONLY"
    )
