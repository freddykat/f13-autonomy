from __future__ import annotations

import json
from pathlib import Path


MANIFEST = Path("validation/manifests/fseries_compatibility_expansion.json")


def _load():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_f13_family_is_core_target():
    payload = _load()
    family = next(item for item in payload["families"] if "F13" in item["chassis"])

    assert family["priority"] == "CORE"
    assert family["observation_reuse"] == "VERY_HIGH"


def test_f10_rwd_xdrive_steering_difference_is_preserved():
    payload = _load()
    family = next(item for item in payload["families"] if "F10" in item["chassis"])

    assert "RWD_EPS_XDRIVE_HYDRAULIC" in family["steering_note"]
    assert family["control_reuse"] == "DRIVETRAIN_DEPENDENT"


def test_no_chassis_code_implies_universal_control_compatibility():
    payload = _load()

    assert payload["global_control_claim"] is False
    assert all(item["control_reuse"] != "UNIVERSAL" for item in payload["families"])


def test_compatibility_requires_variant_specific_keys():
    payload = _load()
    required = set(payload["compatibility_keys_required"])

    assert {
        "build_date",
        "drivetrain",
        "steering_type",
        "icm_generation",
        "dsc_generation",
        "gateway_generation",
        "observed_can_paths",
        "observed_flexray_paths",
        "control_stage",
    }.issubset(required)


def test_fsd_v8_v9_wording_is_ambition_not_validation_claim():
    payload = _load()

    assert "AMBITION_NOT_VALIDATION_CLAIM" in payload["target_experience"]
