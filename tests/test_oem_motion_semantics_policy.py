from __future__ import annotations

import json
from pathlib import Path


MANIFEST = Path("validation/manifests/prototype_001_oem_motion_semantics.json")


def _load():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _all_domains(payload):
    return [entry for group in payload["domains"].values() for entry in group]


def test_oem_motion_semantics_are_passive_only():
    payload = _load()

    assert payload["phase"] == "B1_1_PASSIVE_DISCOVERY"
    assert payload["actuation_authority"] == "NONE"
    assert all(entry["write_capable"] is False for entry in _all_domains(payload))


def test_planner_and_oem_intent_are_not_physical_observations():
    payload = _load()
    by_name = {entry["name"]: entry for entry in _all_domains(payload)}

    assert by_name["OP_PLANNED_LATERAL"]["observed_motion_source"] is False
    assert by_name["BMW_OEM_LATERAL_INTENT"]["observed_motion_source"] is False
    assert by_name["OP_PLANNED_LONGITUDINAL"]["observed_motion_source"] is False
    assert by_name["BMW_OEM_ACC_INTENT"]["observed_motion_source"] is False

    assert by_name["BMW_OBSERVED_LATERAL_MOTION"]["observed_motion_source"] is True
    assert by_name["BMW_OBSERVED_LONGITUDINAL_MOTION"]["observed_motion_source"] is True


def test_bmw_acc_keeps_longitudinal_execution_ownership():
    payload = _load()
    by_name = {entry["name"]: entry for entry in _all_domains(payload)}

    assert by_name["BMW_OEM_ACC_INTENT"]["execution_owner"] == "BMW_OEM_ACC"


def test_rear_steer_and_direct_actuation_remain_forbidden():
    invariants = _load()["invariants"]

    assert invariants["rearSteerActuationAllowed"] is False
    assert invariants["directEpsActuationAllowed"] is False
    assert invariants["directDscActuationAllowed"] is False
    assert invariants["directBrakeActuationAllowed"] is False
    assert invariants["directThrottleActuationAllowed"] is False
    assert invariants["diagnosticWriteAllowed"] is False


def test_unknown_and_semantic_substitution_fail_closed():
    invariants = _load()["invariants"]

    assert invariants["unknownMayBecomeZero"] is False
    assert invariants["plannerMayProveObservedMotion"] is False
    assert invariants["oemIntentMaySubstituteObservedMotion"] is False


def test_semantic_promotion_requires_passive_evidence_and_replay():
    required = set(_load()["promotion_requirements"])

    assert {
        "KNOWN_CONTROLLER_OWNERSHIP",
        "KNOWN_UNITS_AND_COORDINATE_FRAME",
        "REQUEST_VS_FEEDBACK_CLASSIFIED",
        "FRESHNESS_CHARACTERIZED",
        "REPEATABLE_PASSIVE_CORRELATION",
        "INDEPENDENT_PHYSICAL_CORROBORATION",
        "DETERMINISTIC_REPLAY",
        "NO_ACTUATION_PATH",
    }.issubset(required)
