from __future__ import annotations

import json
from pathlib import Path


MANIFEST = Path(__file__).resolve().parents[1] / "validation" / "manifests" / "bmw_flexray_semantic_cross_reference.json"


def _load() -> dict:
    return json.loads(MANIFEST.read_text())


def test_flexray_cross_reference_is_observation_only() -> None:
    data = _load()
    assert data["actuation_authority"] == "NONE"
    assert data["live_tx_allowed"] is False
    assert data["diagnostic_writes_allowed"] is False
    assert data["cross_series_identity_portable"] is False
    assert data["unknown_becomes_zero"] is False


def test_f13_is_not_skipped_by_cross_series_evidence() -> None:
    data = _load()
    ladder = data["promotion_ladder"]
    assert ladder[0] == "CROSS_SERIES_REFERENCE"
    assert "F13_FRAME_CANDIDATE" in ladder
    assert ladder[-1] == "F13_STATE_SOURCE_CANDIDATE"
    assert ladder.index("F13_FRAME_CANDIDATE") < ladder.index("F13_STATE_SOURCE_CANDIDATE")


def test_passive_capture_requires_flexray_provenance() -> None:
    data = _load()
    required = set(data["required_capture_provenance"])
    assert {
        "channel",
        "cycle_identity",
        "slot_or_frame_identity",
        "payload",
        "receive_timestamp",
        "clock_provenance",
        "listen_only_declaration",
        "drop_overflow_loss_visibility",
    } <= required


def test_f13_reference_does_not_claim_wire_identity() -> None:
    data = _load()
    f13 = next(ref for ref in data["references"] if ref["platform"] == "F12/F13")
    assert f13["evidence_state"] == "F13_ARCHITECTURE_EVIDENCED"
    assert "PMA" in f13["observed_controller_families"]
    assert "HSR" in f13["observed_controller_families"]
    assert "message_id" not in f13
    assert "slot" not in f13


def test_bev_donor_vocabulary_is_present_without_portability_claim() -> None:
    data = _load()
    assert "eme_state" in data["semantic_families"]["hybrid_bev_donor_vocabulary"]
    assert "recuperation_regen_limit" in data["semantic_families"]["hybrid_bev_donor_vocabulary"]
    assert data["cross_series_identity_portable"] is False
