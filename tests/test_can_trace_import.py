import pytest

from validation.can_trace_import import (
    build_capture_document,
    import_lines,
    parse_candump_line,
    parse_vector_asc_line,
)


def test_parse_candump_classic_frame():
    frame = parse_candump_line("(12.345678901) can0 123#11223344")
    assert frame is not None
    assert frame.timestamp_ns == 12_345_678_901
    assert frame.channel == "can0"
    assert frame.arbitration_id == 0x123
    assert frame.dlc == 4
    assert frame.data_hex == "11223344"
    assert frame.direction == "Rx"


def test_parse_candump_extended_id_is_inferred_without_decoding_signal_meaning():
    frame = parse_candump_line("(1.000000000) can1 18DAF110#0102030405060708")
    assert frame is not None
    assert frame.is_extended_id is True
    assert frame.arbitration_id == 0x18DAF110


def test_vector_asc_rx_frame():
    frame = parse_vector_asc_line("0.123456 1 123 Rx d 8 11 22 33 44 55 66 77 88")
    assert frame is not None
    assert frame.timestamp_ns == 123_456_000
    assert frame.channel == "asc:1"
    assert frame.direction == "Rx"
    assert frame.dlc == 8
    assert frame.data_hex == "1122334455667788"


def test_vector_asc_extended_id_marker():
    frame = parse_vector_asc_line("2.0 2 18DAF110x Rx d 3 AA BB CC")
    assert frame is not None
    assert frame.is_extended_id is True
    assert frame.arbitration_id == 0x18DAF110


def test_vector_asc_header_lines_are_ignored():
    assert parse_vector_asc_line("date Tue Sep 1 08:00:00.000 2026") is None
    assert parse_vector_asc_line("base hex  timestamps absolute") is None


def test_asc_dlc_mismatch_is_rejected():
    with pytest.raises(ValueError, match="DLC/data mismatch"):
        parse_vector_asc_line("0.1 1 123 Rx d 8 11 22")


def test_non_monotonic_capture_is_rejected():
    with pytest.raises(ValueError, match="monotonic"):
        import_lines(
            [
                "(2.0) can0 123#00",
                "(1.0) can0 123#01",
            ],
            source_format="candump",
        )


def test_capture_document_preserves_listen_only_as_provenance_not_assumption():
    frames = import_lines(["(1.0) can0 123#00"], source_format="candump")
    document = build_capture_document(
        frames,
        capture_id="f13-static-001",
        clock_domain="host_realtime",
        adapter="PCAN-USB-FD",
        listen_only=None,
    )
    assert document["mode"] == "read_only_can_capture_import"
    assert document["listen_only"] is None
    assert document["frame_count"] == 1
    assert document["frames"][0]["timestamp_provenance"] == "capture_tool_timestamp"
