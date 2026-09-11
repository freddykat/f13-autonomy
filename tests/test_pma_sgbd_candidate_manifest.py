from __future__ import annotations

import json
from pathlib import Path


MANIFEST = Path("validation/manifests/f13_pma_sgbd_candidates.template.json")


def _load():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_candidate_manifest_is_passive_and_non_actuating():
    payload = _load()
    invariants = payload["safety_invariants"]

    assert payload["phase"] == "B1_1_PASSIVE_DISCOVERY"
    assert payload["diagnostic_mode"] == "READ_ONLY"
    assert payload["actuation_authority"] == "NONE"
    assert payload["proprietary_data_embedded"] is False

    forbidden = {
        "diagnostic_write_allowed",
        "routine_control_allowed",
        "coding_allowed",
        "clear_faults_allowed",
        "can_tx_allowed",
        "flexray_tx_allowed",
        "eps_actuation_allowed",
        "dsc_actuation_allowed",
        "ias_hsr_actuation_allowed",
        "acc_actuation_allowed",
    }
    assert all(invariants[key] is False for key in forbidden)


def test_unknown_and_diagnostic_timing_fail_closed():
    invariants = _load()["safety_invariants"]

    assert invariants["unknown_may_become_zero"] is False
    assert invariants["catalog_presence_proves_realtime_bus_identity"] is False
    assert invariants["diagnostic_poll_timing_may_prove_request_feedback_order"] is False


def test_evidence_ladder_is_ordered_and_explicit():
    states = _load()["allowed_promotion_states"]

    assert states == [
        "UNSEEN",
        "FRAME_OBSERVED",
        "CORRELATED_WITH_EVENT",
        "DIAGNOSTICALLY_CORROBORATED",
        "CROSS_SOURCE_VALIDATED",
        "REPLAY_STABLE",
        "STATE_SOURCE_CANDIDATE",
    ]


def test_candidate_schema_preserves_provenance_and_semantics():
    required = set(_load()["required_fields"])

    assert {
        "candidate_id",
        "vehicle_platform",
        "controller",
        "controller_address",
        "sgbd_variant",
        "job_name",
        "result_name",
        "unit",
        "scaling_known",
        "semantic_role",
        "catalog_provenance",
        "live_read_status",
        "transport",
        "request_vs_feedback_classified",
        "promotion_state",
    }.issubset(required)


def test_state_source_promotion_requires_cross_source_replay_evidence():
    required = set(_load()["promotion_requirements"]["STATE_SOURCE_CANDIDATE"])

    assert {
        "controller_ownership_known",
        "units_and_scaling_known",
        "request_vs_feedback_classified",
        "freshness_characterized",
        "repeatable_passive_correlation",
        "independent_physical_corroboration",
        "deterministic_replay",
        "no_actuation_path",
    } == required
