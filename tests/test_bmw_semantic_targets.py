import json
from pathlib import Path


PATH = Path(__file__).parents[1] / "validation" / "manifests" / "prototype_001_bmw_semantic_targets.json"


def load_manifest():
    return json.loads(PATH.read_text(encoding="utf-8"))


def test_semantic_targets_are_pre_vehicle_read_only():
    data = load_manifest()
    assert data["mode"] == "read_only_pre_vehicle_correlation"
    assert data["actuation_authority"] == "NONE"
    assert data["vehicle_validated"] is False
    assert data["rules"]["allow_live_transmit"] is False
    assert data["rules"]["automatic_decoder_promotion"] is False


def test_no_target_has_assumed_frame_id_or_transport():
    data = load_manifest()
    for target in data["targets"]:
        assert target["frame_id"] is None
        assert target["transport"] == "UNKNOWN"


def test_every_target_has_physical_correlation_markers():
    data = load_manifest()
    for target in data["targets"]:
        assert target["correlate_with"]
        assert all(isinstance(marker, str) and marker for marker in target["correlate_with"])


def test_vehicle_promotion_requires_review_replay_and_timing():
    rules = load_manifest()["rules"]
    assert rules["require_human_review"] is True
    assert rules["require_replay_regression"] is True
    assert rules["require_measured_timing"] is True
