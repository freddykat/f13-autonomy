from __future__ import annotations

import json
from pathlib import Path


MANIFEST = Path("validation/manifests/prototype_001_beta1_hardware.json")


def _load():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_beta1_is_shadow_only():
    payload = _load()

    assert payload["phase"] == "BETA1_SHADOW"
    assert payload["live_actuation"] is False
    assert payload["acceptance"]["requires_live_steering"] is False
    assert payload["acceptance"]["requires_live_longitudinal"] is False
    assert payload["acceptance"]["requires_parking_control"] is False
    assert payload["acceptance"]["requires_gear_control"] is False


def test_minimum_required_basket_is_small_and_observation_focused():
    payload = _load()
    required = {
        item["item"]
        for item in payload["hardware"]
        if item["priority"] == "REQUIRED"
    }

    assert required == {
        "COMMA_FOUR",
        "PASSIVE_CAN_LOGGER",
        "PROTECTED_POWER_AND_BREAKOUT_HARNESS",
        "ENET_DIAGNOSTIC_ACCESS",
    }


def test_flexray_is_conditional_not_first_day_requirement():
    payload = _load()
    flexray = next(
        item for item in payload["hardware"]
        if item["item"] == "PASSIVE_FLEXRAY_RX"
    )

    assert flexray["priority"] == "CONDITIONAL"
    assert flexray["activation_condition"] == "CAN_EVIDENCE_INSUFFICIENT_OR_AMBIGUOUS"
    assert flexray["beta1_blocker_if_missing"] is False


def test_expansion_hardware_is_deferred_from_beta1():
    payload = _load()
    priorities = {item["item"]: item["priority"] for item in payload["hardware"]}

    for item in (
        "KAFAS2_RETROFIT",
        "SURROUND_CAMERAS",
        "LIDAR_DEPTH",
        "CHESTNUT_EGPU",
        "TESLA_HW4_BENCHMARK_HARDWARE",
        "PARKING_ACTUATION_HARDWARE",
    ):
        assert priorities[item] == "DEFER"


def test_beta1_does_not_require_duplicate_perception_hardware():
    payload = _load()
    acceptance = payload["acceptance"]

    assert acceptance["requires_kafas2"] is False
    assert acceptance["requires_lidar"] is False
    assert acceptance["requires_surround_cameras"] is False
    assert acceptance["requires_external_gpu"] is False


def test_beta1_acceptance_requires_replay_and_shadow_evidence():
    payload = _load()
    required = set(payload["acceptance"]["requires"])

    assert {
        "SYNCHRONIZED_COMMA_AND_BMW_CAPTURE",
        "CORE_BMW_EGO_STATE_EVIDENCE",
        "TRANSPORT_PROVENANCE",
        "OPENPILOT_SHADOW_PROPOSAL",
        "BMW_CONTROL_INTENT_SHADOW",
        "DETERMINISTIC_REPLAY",
    }.issubset(required)
