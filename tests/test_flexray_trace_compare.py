from validation.flexray_trace_compare import compare_traces


def frame(seq, t, slot, payload="0102", *, cycle=1, channel="A", source="ref"):
    return {
        "host_time_ns": t,
        "capture_sequence": seq,
        "slot_id": slot,
        "cycle": cycle,
        "payload_length": len(bytes.fromhex(payload)),
        "payload_hex": payload,
        "channel": channel,
        "source": source,
    }


def test_exact_trace_with_constant_clock_offset_is_state_source_candidate():
    reference = [
        frame(0, 1_000_000, 1),
        frame(1, 2_000_000, 2),
        frame(2, 3_000_000, 3),
    ]
    candidate = [
        frame(0, 11_000_000, 1, source="candidate"),
        frame(1, 12_000_000, 2, source="candidate"),
        frame(2, 13_000_000, 3, source="candidate"),
    ]

    report = compare_traces(reference, candidate)

    assert report.exact_frame_fidelity
    assert report.clock_offset_ns == 10_000_000
    assert report.max_abs_residual_ns == 0
    assert report.classify() == "STATE_SOURCE_CANDIDATE"


def test_missing_frame_is_observation_only():
    reference = [frame(0, 1_000_000, 1), frame(1, 2_000_000, 2)]
    candidate = [frame(0, 1_000_000, 1, source="candidate")]

    report = compare_traces(reference, candidate)

    assert len(report.missing_keys) == 1
    assert not report.exact_frame_fidelity
    assert report.classify() == "OBSERVATION_ONLY"


def test_payload_mismatch_is_observation_only():
    reference = [frame(0, 1_000_000, 1, "0102")]
    candidate = [frame(0, 1_000_000, 1, "0103", source="candidate")]

    report = compare_traces(reference, candidate)

    assert len(report.payload_mismatches) == 1
    assert report.classify() == "OBSERVATION_ONLY"


def test_jitter_can_be_replay_trusted_without_being_state_source_candidate():
    reference = [
        frame(0, 0, 1),
        frame(1, 10_000_000, 2),
        frame(2, 20_000_000, 3),
    ]
    candidate = [
        frame(0, 100_000_000, 1, source="candidate"),
        frame(1, 113_000_000, 2, source="candidate"),
        frame(2, 120_000_000, 3, source="candidate"),
    ]

    report = compare_traces(reference, candidate)

    assert report.exact_frame_fidelity
    assert report.max_abs_residual_ns == 3_000_000
    assert report.classify() == "REPLAY_TRUSTED"


def test_invalid_candidate_trace_is_rejected():
    reference = [frame(0, 1_000_000, 1)]
    candidate = [frame(0, 1_000_000, 1, source="candidate")]
    candidate[0]["payload_hex"] = "not-hex"

    report = compare_traces(reference, candidate)

    assert report.candidate_errors
    assert report.classify() == "REJECTED"


def test_repeated_cycle_slot_uses_occurrence_ordinal():
    reference = [
        frame(0, 1_000_000, 1, "0102", cycle=0),
        frame(1, 2_000_000, 1, "0304", cycle=0),
    ]
    candidate = [
        frame(0, 11_000_000, 1, "0102", cycle=0, source="candidate"),
        frame(1, 12_000_000, 1, "0304", cycle=0, source="candidate"),
    ]

    report = compare_traces(reference, candidate)

    assert report.matched_count == 2
    assert report.exact_frame_fidelity
