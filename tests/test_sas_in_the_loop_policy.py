from __future__ import annotations

import json
from pathlib import Path


MANIFEST = Path("validation/manifests/sas_in_the_loop_policy.json")


def _load():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_sas_is_teacher_not_live_f13_controller():
    payload = _load()

    assert payload["teacher_role"] == "SEMANTIC_REFERENCE_AND_SHADOW_VALIDATOR"
    assert payload["live_f13_actuation"] is False
    assert payload["direct_gseries_to_f13_forwarding"] is False
    assert payload["protocol_equivalence_claim"] is False


def test_security_bypass_is_not_part_of_research():
    payload = _load()

    assert payload["security_bypass"] is False
    forbidden = set(payload["forbidden"])
    assert {
        "SECURE_BOOT_BYPASS",
        "HSM_BYPASS",
        "ANTI_THEFT_BYPASS",
        "VEHICLE_IDENTITY_CLONING_FOR_ACCESS",
    }.issubset(forbidden)


def test_virtual_vehicle_context_is_bench_only_and_benign():
    payload = _load()
    level = next(item for item in payload["levels"] if item["level"] == "L2_VIRTUAL_VEHICLE_CONTEXT")

    assert level["powered_ecu_required"] is True
    assert "BENIGN_STATE_REPLAY" in level["allowed"]
    assert "DEPENDENCY_DISCOVERY" in level["allowed"]


def test_direct_cross_generation_command_translation_is_forbidden():
    payload = _load()
    forbidden = set(payload["forbidden"])

    assert "DIRECT_SAS_TO_F13_COMMAND_FORWARDING" in forbidden
    assert "GENERIC_GSERIES_TO_FSERIES_COMMAND_TRANSLATION" in forbidden


def test_cross_generation_stage_is_semantic_only():
    payload = _load()
    level = next(item for item in payload["levels"] if item["level"] == "L4_CROSS_GENERATION_SEMANTIC_COMPARISON")

    assert set(level["allowed"]) == {
        "SEMANTIC_TEMPLATE_MATCHING",
        "F13_HYPOTHESIS_RANKING",
        "OFFLINE_COMPARISON",
    }
