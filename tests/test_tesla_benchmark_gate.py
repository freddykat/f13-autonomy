import copy
import json
from pathlib import Path

from validation.tesla_benchmark_gate import evaluate_tesla_benchmark


ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "validation" / "corpus" / "tesla_benchmark_smoke.json"
LOCK = ROOT / "upstream" / "openpilot.lock.json"


def baseline_commit():
    return json.loads(LOCK.read_text(encoding="utf-8"))["openpilot"]["commit"]


def episode():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def evaluate(candidate):
    return evaluate_tesla_benchmark(candidate, expected_openpilot_commit=baseline_commit())


def test_synthetic_same_episode_fixture_is_comparison_ready():
    report = evaluate(episode())
    assert report.classification == "BEHAVIOURAL_COMPARISON_READY"
    assert report.comparable_signal_count == 2
    assert report.cross_validated_signal_count == 1
    assert report.actuation_authority == "NONE"


def test_matched_scenario_never_claims_same_episode_timing():
    candidate = episode()
    candidate["comparison_mode"] = "MATCHED_SCENARIO"
    candidate["alignment"] = {"method": "MATCHED_SCENARIO_ONLY", "max_error_ms": None}

    report = evaluate(candidate)
    assert report.classification == "SCENARIO_BENCHMARK_ONLY"
    assert "NOT_THE_SAME_PHYSICAL_EPISODE" in report.reasons


def test_observed_drop_downgrades_episode():
    candidate = episode()
    candidate["tesla"]["rx_dropped_count"] = 1

    report = evaluate(candidate)
    assert report.classification == "OBSERVATION_ONLY"
    assert "TESLA_CAPTURE_LOSS_OBSERVED" in report.reasons


def test_unknown_loss_counters_do_not_mean_zero():
    candidate = episode()
    candidate["tesla"]["rx_dropped_count"] = None

    report = evaluate(candidate)
    assert report.classification == "OBSERVATION_ONLY"
    assert "TESLA_LOSS_COUNTERS_UNKNOWN" in report.reasons


def test_untrusted_usb_batch_timing_cannot_qualify_alignment():
    candidate = episode()
    candidate["tesla"]["timing_provenance"] = "USB_BATCH_WALL_CLOCK"

    report = evaluate(candidate)
    assert report.classification == "OBSERVATION_ONLY"
    assert "TIMING_NOT_QUALIFIED" in report.reasons


def test_openpilot_skipped_model_frame_downgrades_episode():
    candidate = episode()
    candidate["openpilot"]["model_skipped_frame_count"] = 1

    report = evaluate(candidate)
    assert report.classification == "OBSERVATION_ONLY"
    assert "OPENPILOT_FRAME_LOSS_OBSERVED" in report.reasons


def test_unknown_signal_must_remain_null():
    candidate = episode()
    candidate["signals"][2]["value"] = False

    report = evaluate(candidate)
    assert report.classification == "REJECTED"
    assert "UNKNOWN must preserve value as null" in report.errors[0]


def test_tesla_write_path_is_rejected():
    candidate = episode()
    candidate["tesla"]["write_path_present"] = True

    report = evaluate(candidate)
    assert report.classification == "REJECTED"
    assert "write path is prohibited" in report.errors[0]


def test_different_openpilot_commit_is_rejected():
    candidate = copy.deepcopy(episode())
    candidate["openpilot"]["baseline_commit"] = "0" * 40

    report = evaluate(candidate)
    assert report.classification == "REJECTED"
    assert "differs from the locked project baseline" in report.errors[0]
