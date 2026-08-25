from validation.flexray_capture_validator import validate_records


def frame(seq: int, time_ns: int, payload: str = "00112233") -> dict:
    return {
        "host_time_ns": time_ns,
        "source_time_ns": None,
        "channel": "A",
        "slot_id": 42,
        "cycle": 1,
        "payload_hex": payload,
        "payload_length": len(bytes.fromhex(payload)),
        "frame_flags": [],
        "capture_sequence": seq,
        "source": "synthetic",
    }


def test_valid_trace_passes():
    report = validate_records([frame(1, 100), frame(2, 200), frame(3, 300)])
    assert report.passed
    assert report.sequence_gaps == []


def test_sequence_gap_is_observable_warning_not_silent_failure():
    report = validate_records([frame(10, 100), frame(12, 200)])
    assert report.passed
    assert report.sequence_gaps == [(10, 12)]
    assert report.warnings


def test_timestamp_regression_fails():
    report = validate_records([frame(1, 200), frame(2, 199)])
    assert not report.passed
    assert any("regressed" in error for error in report.errors)


def test_duplicate_sequence_fails():
    report = validate_records([frame(1, 100), frame(1, 200)])
    assert not report.passed
    assert any("did not increase" in error for error in report.errors)


def test_payload_length_mismatch_fails():
    bad = frame(1, 100)
    bad["payload_length"] = 99
    report = validate_records([bad])
    assert not report.passed
    assert any("payload length mismatch" in error for error in report.errors)


def test_invalid_hex_fails():
    bad = frame(1, 100)
    bad["payload_hex"] = "not-hex"
    report = validate_records([bad])
    assert not report.passed
    assert any("valid hex" in error for error in report.errors)
