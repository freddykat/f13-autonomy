import pytest

from validation.can_trace_compare import (
    CanTraceComparisonError,
    CanTraceComparisonReport,
    compare_can_captures,
)
from validation.capture_quality_evaluator import (
    CaptureQualityError,
    evaluate_can_capture,
)


def capture(
    capture_id,
    payloads,
    *,
    channel="can0",
    timestamps=None,
    timing="capture_tool_timestamp",
    reference_quality=False,
):
    timestamps = timestamps or [100 + index * 100 for index in range(len(payloads))]
    return {
        "schema_version": 2,
        "capture_id": capture_id,
        "mode": "read_only_can_capture_import",
        "clock_domain": f"{capture_id}-clock",
        "adapter": f"{capture_id}-adapter",
        "listen_only": True,
        "capture_quality": "FULL_RATE_CANDIDATE" if reference_quality else "OBSERVATION_ONLY",
        "filter_mode": "SINGLE_ID_HARDWARE" if reference_quality else "UNKNOWN",
        "rx_queue_depth": 64 if reference_quality else None,
        "rx_dropped_count": 0 if reference_quality else None,
        "rx_overflow_count": 0 if reference_quality else None,
        "frame_count": len(payloads),
        "frames": [
            {
                "timestamp_ns": timestamp,
                "timestamp_provenance": timing,
                "source_format": "fixture",
                "channel": channel,
                "direction": "Rx",
                "arbitration_id": 0x123,
                "is_extended_id": False,
                "is_remote_frame": False,
                "dlc": 1,
                "data_hex": payload,
            }
            for timestamp, payload in zip(timestamps, payloads)
        ],
    }


def test_exact_simultaneous_comparison_promotes_matching_candidate():
    reference = capture("vector-ref", ["01", "02", "03"], channel="asc:1", reference_quality=True)
    candidate = capture("panda-candidate", ["01", "02", "03"], channel="can0")

    comparison = compare_can_captures(
        reference,
        candidate,
        simultaneous=True,
        reference_channel_map={"asc:1": "vehicle-can"},
        candidate_channel_map={"can0": "vehicle-can"},
    )

    assert comparison.frame_fidelity == "EXACT"
    assert comparison.matched_frame_count == 3
    assert comparison.actuation_authority == "NONE"
    quality = evaluate_can_capture(candidate, reference_comparison=comparison)
    assert quality.evaluated_quality == "FULL_RATE_CANDIDATE"
    assert quality.metrics["reference_frame_fidelity"] == "EXACT"


def test_missing_frame_does_not_shift_every_later_payload():
    reference = capture("ref", ["01", "02", "03", "04"], reference_quality=True)
    candidate = capture("candidate", ["01", "03", "04"])
    comparison = compare_can_captures(reference, candidate, simultaneous=True)

    assert comparison.frame_fidelity == "MISMATCH"
    assert comparison.missing_frame_count == 1
    assert comparison.extra_frame_count == 0
    assert comparison.payload_mismatch_count == 0
    assert comparison.matched_frame_count == 3
    assert evaluate_can_capture(candidate, reference_comparison=comparison).evaluated_quality == "LOSSY"


def test_payload_divergence_is_reported_byte_for_byte():
    reference = capture("ref", ["01", "02"], reference_quality=True)
    candidate = capture("candidate", ["01", "FF"])
    comparison = compare_can_captures(reference, candidate, simultaneous=True)

    assert comparison.frame_fidelity == "MISMATCH"
    assert comparison.payload_mismatch_count == 1
    assert comparison.mismatch_examples[0]["reference"] == "02"
    assert comparison.mismatch_examples[0]["candidate"] == "FF"


def test_extra_frame_is_reported_without_bmw_signal_assumptions():
    reference = capture("ref", ["01", "02"], reference_quality=True)
    candidate = capture("candidate", ["01", "AA", "02"])
    comparison = compare_can_captures(reference, candidate, simultaneous=True)
    assert comparison.frame_fidelity == "MISMATCH"
    assert comparison.extra_frame_count == 1


def test_non_simultaneous_traces_cannot_claim_exact_fidelity():
    reference = capture("ref", ["01"], reference_quality=True)
    candidate = capture("candidate", ["01"])
    comparison = compare_can_captures(reference, candidate, simultaneous=False)
    assert comparison.frame_fidelity == "NOT_SIMULTANEOUS"
    assert evaluate_can_capture(candidate, reference_comparison=comparison).evaluated_quality == "OBSERVATION_ONLY"


def test_unqualified_reference_cannot_promote_candidate():
    reference = capture("unknown-ref", ["01"])
    candidate = capture("candidate", ["01"])
    comparison = compare_can_captures(reference, candidate, simultaneous=True)
    assert comparison.frame_fidelity == "UNQUALIFIED_REFERENCE"
    assert evaluate_can_capture(candidate, reference_comparison=comparison).evaluated_quality == "OBSERVATION_ONLY"


def test_trusted_per_frame_timing_removes_constant_clock_offset():
    reference = capture(
        "ref", ["01", "02", "03"], timestamps=[100, 200, 300],
        timing="reference_export", reference_quality=True,
    )
    candidate = capture(
        "candidate", ["01", "02", "03"], timestamps=[1_100, 1_205, 1_295],
        timing="hardware_timestamp",
    )
    comparison = compare_can_captures(reference, candidate, simultaneous=True)
    assert comparison.timing_fidelity == "PER_FRAME_COMPARABLE"
    assert comparison.clock_offset_ns == 1_000
    assert comparison.median_absolute_timing_residual_ns == 5
    assert comparison.max_absolute_timing_residual_ns == 5


def test_host_capture_timestamps_do_not_claim_timing_fidelity():
    reference = capture("ref", ["01"], reference_quality=True)
    candidate = capture("candidate", ["01"])
    comparison = compare_can_captures(reference, candidate, simultaneous=True)
    assert comparison.frame_fidelity == "EXACT"
    assert comparison.timing_fidelity == "TIMING_UNVERIFIED"
    assert comparison.clock_offset_ns is None


def test_channel_map_collision_is_rejected():
    reference = capture("ref", ["01"], reference_quality=True)
    candidate = capture("candidate", ["01"])
    with pytest.raises(CanTraceComparisonError, match="multiple source channels"):
        compare_can_captures(
            reference,
            candidate,
            simultaneous=True,
            reference_channel_map={"asc:1": "vehicle", "asc:2": "vehicle"},
        )


def test_comparison_cannot_be_reused_for_another_capture_id():
    reference = capture("ref", ["01"], reference_quality=True)
    candidate = capture("candidate", ["01"])
    other = capture("other", ["01"])
    comparison = compare_can_captures(reference, candidate, simultaneous=True)
    with pytest.raises(CaptureQualityError, match="candidate_capture_id"):
        evaluate_can_capture(other, reference_comparison=comparison)


def test_manual_can_exact_claim_is_rejected():
    candidate = capture("candidate", ["01"])
    with pytest.raises(CaptureQualityError, match="must come from can_trace_compare"):
        evaluate_can_capture(
            candidate,
            supplemental_evidence={"reference_frame_fidelity": "EXACT"},
        )


def test_exact_report_round_trips_through_strict_json_contract():
    reference = capture("ref", ["01", "02"], reference_quality=True)
    candidate = capture("candidate", ["01", "02"])
    original = compare_can_captures(reference, candidate, simultaneous=True)
    restored = CanTraceComparisonReport.from_dict(original.to_dict())
    assert restored == original


def test_internally_inconsistent_exact_report_is_rejected():
    reference = capture("ref", ["01"], reference_quality=True)
    candidate = capture("candidate", ["01"])
    raw = compare_can_captures(reference, candidate, simultaneous=True).to_dict()
    raw["missing_frame_count"] = 1
    with pytest.raises(CanTraceComparisonError, match="EXACT report invariants"):
        CanTraceComparisonReport.from_dict(raw)
