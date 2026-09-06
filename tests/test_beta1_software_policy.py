from __future__ import annotations

import json
from pathlib import Path


MANIFEST = Path("validation/manifests/prototype_001_beta1_software.json")


def _load():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_beta1_software_is_read_only():
    payload = _load()

    assert payload["phase"] == "BETA1_SHADOW_SOFTWARE"
    assert all(component["write_capable"] is False for component in payload["components"])


def test_required_minimum_components_are_present():
    payload = _load()
    required = {
        component["name"]
        for component in payload["components"]
        if component["required"]
    }

    assert {
        "locked_openpilot_baseline",
        "bmw_transport_ingest",
        "bmw_core_ego_decoders",
        "bmw_vehicle_state",
        "bmw_carstate",
        "bmw_interface",
        "bmw_control_intent_shadow",
        "deterministic_replay",
    }.issubset(required)


def test_bmw_interface_stays_dashcam_only():
    payload = _load()
    interface = next(
        component for component in payload["components"]
        if component["name"] == "bmw_interface"
    )

    assert interface["dashcamOnly"] is True
    assert interface["write_capable"] is False


def test_radar_and_blindspot_are_conditional_not_beta1_blockers():
    payload = _load()
    by_name = {component["name"]: component for component in payload["components"]}

    assert by_name["bmw_acc_radar"]["required"] is False
    assert by_name["bmw_blindspot"]["required"] is False


def test_control_intent_is_shadow_only():
    payload = _load()
    intent = next(
        component for component in payload["components"]
        if component["name"] == "bmw_control_intent_shadow"
    )

    assert intent["authority"] == "SHADOW"
    assert intent["write_capable"] is False


def test_live_control_paths_are_explicitly_forbidden():
    payload = _load()
    forbidden = set(payload["forbidden"])

    assert {
        "BMW_CARCONTROLLER",
        "SENDCAN",
        "CAN_TX_ENCODER",
        "FLEXRAY_TX_ENCODER",
        "DIAGNOSTIC_WRITE",
        "EPS_ACTUATION",
        "DSC_ACTUATION",
        "DME_ACTUATION",
        "GEAR_ACTUATION",
        "PARKING_ACTUATION",
    }.issubset(forbidden)


def test_acceptance_requires_no_actuation_path():
    payload = _load()

    assert "NO_ACTUATION_PATH" in payload["acceptance"]
    assert "DETERMINISTIC_REPLAY" in payload["acceptance"]
    assert "VALIDATED_BMW_EGO_STATE" in payload["acceptance"]
