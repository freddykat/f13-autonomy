import json
from pathlib import Path


PATH = Path(__file__).parents[1] / "validation" / "manifests" / "prototype_001_bmw_signal_candidates.json"


def load_candidates():
    return json.loads(PATH.read_text(encoding="utf-8"))


def test_candidate_manifest_is_read_only_and_pre_vehicle():
    data = load_candidates()
    assert data["schema_version"] == 1
    assert data["mode"] == "read_only_research_candidates"
    assert data["actuation_authority"] == "NONE"
    assert "VEHICLE_VALIDATED" not in data["allowed_confidence"]
    assert data["candidates"]


def test_no_candidate_can_be_marked_vehicle_validated_before_capture():
    data = load_candidates()
    assert all(item["confidence"] != "VEHICLE_VALIDATED" for item in data["candidates"])


def test_documented_f13_candidates_have_pinned_evidence():
    data = load_candidates()
    documented = [item for item in data["candidates"] if item["f13_family_documented"]]
    assert documented
    for item in documented:
        assert item["confidence"] == "DOCUMENTED_FAMILY"
        assert item["evidence"]
        for evidence in item["evidence"]:
            assert len(evidence["snapshot"]) == 40
            assert evidence["source"]
            assert evidence["path"]


def test_diagnostic_addresses_are_not_presented_as_bus_frame_ids():
    data = load_candidates()
    for item in data["candidates"]:
        assert "can_id" not in item
        assert item["transport"] == "UNKNOWN"
