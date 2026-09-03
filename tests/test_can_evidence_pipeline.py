import copy
import json
from pathlib import Path

import pytest

from validation.can_evidence_pipeline import (
    CanEvidencePipelineError,
    run_can_evidence_pipeline,
)


ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "validation" / "corpus" / "can_beta0"
PROFILE = "prototype-001-f13-650i-xdrive-2012"


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def inputs():
    return (
        load(CORPUS / "reference.json"),
        load(CORPUS / "candidate.json"),
        load(ROOT / "validation" / "manifests" / "prototype_001_bmw_decoders.json"),
        load(CORPUS / "pair_spec.json"),
    )


def run(reference=None, candidate=None, manifest=None, pair_spec=None):
    defaults = inputs()
    return run_can_evidence_pipeline(
        reference or defaults[0],
        candidate or defaults[1],
        manifest or defaults[2],
        pair_spec or defaults[3],
        vehicle_profile=PROFILE,
    )


def test_golden_beta0_corpus_matches_expected_summary():
    report = run()
    expected = load(CORPUS / "expected_summary.json")
    actual = {
        **report["summary"],
        "actuation_authority": report["actuation_authority"],
        "beta_stage": report["beta_stage"],
        "verdict": report["verdict"],
    }
    assert actual == expected
    assert report["capture_pair_manifest"]["actuation_authority"] == "NONE"
    assert report["comparison"]["actuation_authority"] == "NONE"
    assert report["decoded_observations"]["actuation_authority"] == "NONE"


def test_candidate_payload_loss_rejects_whole_pipeline():
    reference, candidate, manifest, pair_spec = inputs()
    candidate["frames"].pop(1)
    candidate["frame_count"] = 2
    report = run(reference, candidate, manifest, pair_spec)
    assert report["verdict"] == "REJECTED"
    assert report["summary"]["frame_fidelity"] == "MISMATCH"
    assert report["summary"]["capture_quality"] == "LOSSY"


def test_manual_pair_assertion_stays_observation_only():
    reference, candidate, manifest, pair_spec = inputs()
    pair_spec["sync_method"] = "MANUAL_ASSERTION"
    report = run(reference, candidate, manifest, pair_spec)
    assert report["verdict"] == "OBSERVATION_ONLY"
    assert report["summary"]["frame_fidelity"] == "UNVERIFIED_PAIR"


def test_unknown_pair_spec_field_fails_closed():
    reference, candidate, manifest, pair_spec = inputs()
    pair_spec["trust_me"] = True
    with pytest.raises(CanEvidencePipelineError, match="unknown fields"):
        run(reference, candidate, manifest, pair_spec)


def test_production_manifest_remains_empty_of_bmw_signal_guesses():
    _, _, manifest, _ = inputs()
    assert manifest["signals"] == []
    report = run()
    assert report["decoded_observations"]["executable_decoder_count"] == 0
    assert report["decoded_observations"]["observation_count"] == 0


def test_input_objects_are_not_mutated():
    reference, candidate, manifest, pair_spec = inputs()
    originals = copy.deepcopy((reference, candidate, manifest, pair_spec))
    run(reference, candidate, manifest, pair_spec)
    assert (reference, candidate, manifest, pair_spec) == originals
