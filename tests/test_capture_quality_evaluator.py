from validation.capture_quality_evaluator import (
    evaluate_can_capture,
    evaluate_flexray_capture,
)


def can_capture(
    *,
    quality="UNKNOWN",
    filter_mode="UNKNOWN",
    dropped=None,
    overflow=None,
    listen_only=True,
):
    return {
        "schema_version": 2,
        "capture_id": "can-fixture",
        "mode": "read_only_can_capture_import",
        "clock_domain": "fixture_clock",
        "adapter": "fixture_adapter",
        "listen_only": listen_only,
        "capture_quality": quality,
        "filter_mode": filter_mode,
        "rx_queue_depth": 64,
        "rx_dropped_count": dropped,
        "rx_overflow_count": overflow,
        "frame_count": 2,
        "frames": [
            {
                "timestamp_ns": 100,
                "timestamp_provenance": "capture_tool_timestamp",
                "source_format": "candump",
                "channel": "can0",
                "direction": "Rx",
                "arbitration_id": 0x123,
                "is_extended_id": False,
                "is_remote_frame": False,
                "dlc": 1,
                "data_hex": "01",
            },
            {
                "timestamp_ns": 200,
                "timestamp_provenance": "capture_tool_timestamp",
                "source_format": "candump",
                "channel": "can0",
                "direction": "Rx",
                "arbitration_id": 0x123,
                "is_extended_id": False,
                "is_remote_frame": False,
                "dlc": 1,
                "data_hex": "02",
            },
        ],
    }


def flexray_frame(sequence, timestamp, *, timing="per_frame_monotonic"):
    return {
        "host_time_ns": timestamp,
        "source_time_ns": None,
        "channel": "A",
        "slot_id": 42,
        "cycle": sequence % 64,
        "payload_hex": "0011",
        "payload_length": 2,
        "frame_flags": [],
        "capture_sequence": sequence,
        "source": "fixture",
        "timing_provenance": timing,
    }


def flexray_provenance(**overrides):
    result = {
        "capture_id": "flexray-fixture",
        "capture_quality": "UNKNOWN",
        "listen_only": True,
        "filter_mode": "ACCEPT_ALL",
        "rx_queue_depth": 256,
        "rx_dropped_count": 0,
        "rx_overflow_count": 0,
    }
    result.update(overrides)
    return result


def test_unknown_counters_and_filter_remain_observation_only():
    report = evaluate_can_capture(can_capture())
    assert report.evaluated_quality == "OBSERVATION_ONLY"
    assert "rx_dropped_count is unavailable" in report.unknown_evidence
    assert report.actuation_authority == "NONE"


def test_single_id_hardware_filter_and_zero_counters_reach_full_rate_candidate():
    report = evaluate_can_capture(
        can_capture(
            quality="FULL_RATE_CANDIDATE",
            filter_mode="SINGLE_ID_HARDWARE",
            dropped=0,
            overflow=0,
        )
    )
    assert report.evaluated_quality == "FULL_RATE_CANDIDATE"
    assert report.timing_quality == "TIMING_UNVERIFIED"


def test_full_rate_declaration_alone_cannot_promote_unknown_loss_counters():
    report = evaluate_can_capture(
        can_capture(
            quality="FULL_RATE_CANDIDATE",
            filter_mode="SINGLE_ID_HARDWARE",
        )
    )
    assert report.evaluated_quality == "OBSERVATION_ONLY"


def test_observed_drop_forces_lossy_even_when_declared_full_rate():
    report = evaluate_can_capture(
        can_capture(
            quality="FULL_RATE_CANDIDATE",
            filter_mode="SINGLE_ID_HARDWARE",
            dropped=3,
            overflow=0,
        )
    )
    assert report.evaluated_quality == "LOSSY"
    assert any("3 dropped" in reason for reason in report.negative_evidence)


def test_failed_expected_rate_check_forces_lossy():
    report = evaluate_can_capture(
        can_capture(filter_mode="SINGLE_ID_HARDWARE", dropped=0, overflow=0),
        supplemental_evidence={"expected_rate_checked": False},
    )
    assert report.evaluated_quality == "LOSSY"


def test_unknown_listen_only_state_caps_capture_at_observation_only():
    report = evaluate_can_capture(
        can_capture(
            filter_mode="SINGLE_ID_HARDWARE",
            dropped=0,
            overflow=0,
            listen_only=None,
        )
    )
    assert report.evaluated_quality == "OBSERVATION_ONLY"


def test_timestamp_regression_forces_lossy_and_invalid_timing():
    capture = can_capture(
        filter_mode="SINGLE_ID_HARDWARE",
        dropped=0,
        overflow=0,
    )
    capture["frames"][1]["timestamp_ns"] = 50
    report = evaluate_can_capture(capture)
    assert report.evaluated_quality == "LOSSY"
    assert report.timing_quality == "INVALID"


def test_malformed_payload_is_audited_as_lossy():
    capture = can_capture()
    capture["frames"][0]["data_hex"] = "not-hex"
    report = evaluate_can_capture(capture)
    assert report.evaluated_quality == "LOSSY"
    assert report.metrics["structural_error_count"] == 1


def test_flexray_adapter_sequence_gap_forces_lossy():
    records = [flexray_frame(1, 100), flexray_frame(3, 200)]
    report = evaluate_flexray_capture(
        records,
        provenance=flexray_provenance(),
        supplemental_evidence={"sequence_provenance": "ADAPTER_MONOTONIC"},
    )
    assert report.evaluated_quality == "LOSSY"
    assert report.metrics["sequence_gap_count"] == 1


def test_pico_style_row_ordinal_and_batch_timing_do_not_claim_full_rate():
    records = [
        flexray_frame(0, 100, timing="usb_batch_wall_clock"),
        flexray_frame(1, 100, timing="usb_batch_wall_clock"),
    ]
    provenance = flexray_provenance(
        rx_dropped_count=None,
        rx_overflow_count=None,
    )
    report = evaluate_flexray_capture(
        records,
        provenance=provenance,
        supplemental_evidence={"sequence_provenance": "ROW_ORDINAL"},
    )
    assert report.evaluated_quality == "OBSERVATION_ONLY"
    assert report.timing_quality == "TIMING_UNVERIFIED"


def test_clean_adapter_sequence_and_zero_counters_can_qualify_flexray():
    records = [flexray_frame(10, 100), flexray_frame(11, 200)]
    report = evaluate_flexray_capture(
        records,
        provenance=flexray_provenance(),
        supplemental_evidence={"sequence_provenance": "ADAPTER_MONOTONIC"},
    )
    assert report.evaluated_quality == "FULL_RATE_CANDIDATE"
    assert report.timing_quality == "PER_FRAME_CANDIDATE"
    assert report.actuation_authority == "NONE"


def test_declared_observation_only_is_a_ceiling_without_exact_reference():
    capture = can_capture(
        quality="OBSERVATION_ONLY",
        filter_mode="SINGLE_ID_HARDWARE",
        dropped=0,
        overflow=0,
    )
    report = evaluate_can_capture(capture)
    assert report.evaluated_quality == "OBSERVATION_ONLY"


def test_sequence_gap_is_negative_even_when_sequence_origin_is_unknown():
    report = evaluate_can_capture(
        can_capture(
            filter_mode="SINGLE_ID_HARDWARE",
            dropped=0,
            overflow=0,
        ),
        supplemental_evidence={"sequence_gap_count": 1},
    )
    assert report.evaluated_quality == "LOSSY"


def test_report_is_json_ready_and_never_grants_control():
    report = evaluate_can_capture(can_capture()).to_dict()
    assert report["actuation_authority"] == "NONE"
    assert report["metrics"]["reference_frame_fidelity"] == "NOT_COMPARED"
