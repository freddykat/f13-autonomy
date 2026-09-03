import copy

import pytest

from validation.offline_can_decoder import OfflineDecodeError, decode_capture


PROFILE = "prototype-001-f13-650i-xdrive-2012"


def evidence(kind="community_reference", reference="tests/fixture", group="fixture"):
    return {
        "kind": kind,
        "reference": reference,
        "independence_group": group,
        "capture_id": None,
        "sha256": None,
        "notes": "Synthetic test evidence only.",
    }


def signal(status="SEMANTIC_CANDIDATE"):
    return {
        "decoder_id": "fixture.can.signal.v1",
        "signal": "fixture_signal",
        "state_path": "chassis.fixtureSignal",
        "transport": "CAN",
        "bus": "FIXTURE_BUS",
        "channel": "can0",
        "frame": {
            "arbitration_id": 0x123,
            "is_extended_id": False,
            "dlc": 8,
            "direction": "Rx",
        },
        "layout": {
            "start_byte": 1,
            "start_bit_in_byte": 0,
            "absolute_start_bit": 8,
            "bit_length": 16,
            "bit_numbering": "lsb0",
            "byte_order": "little_endian",
            "signed": False,
        },
        "conversion": {
            "scale": 0.1,
            "offset": 0.0,
            "unit": "fixture_unit",
            "choices": {},
        },
        "validity": {
            "physical_min": 0.0,
            "physical_max": 1000.0,
            "stale_after_ns": 100_000_000,
            "invalid_raw_values": [65535],
        },
        "evidence": [evidence()],
        "vehicle_applicability": {
            "profile_ids": [PROFILE],
            "ecu_part_numbers": [],
            "software_versions": [],
            "notes": "Synthetic fixture only.",
        },
        "decoder_version": "0.1.0",
        "validation_status": status,
        "notes": "Synthetic fixture; not a BMW decode.",
    }


def manifest(sig=None):
    return {
        "schema_version": 1,
        "manifest_id": "fixture-offline-decode",
        "mode": "read_only_decoder_manifest",
        "vehicle_profiles": {
            PROFILE: {
                "make": "BMW",
                "chassis": "F13",
                "model": "650i xDrive",
                "model_year": 2012,
                "powertrain": "N63 non-TU",
                "notes": "Synthetic test profile.",
            }
        },
        "signals": [] if sig is None else [sig],
    }


def capture(data_hex="0034120000000000", channel="can0", quality="FULL_RATE_CANDIDATE"):
    return {
        "schema_version": 2,
        "capture_id": "fixture-capture",
        "mode": "read_only_can_capture_import",
        "clock_domain": "fixture_clock",
        "adapter": "fixture_adapter",
        "listen_only": True,
        "capture_quality": quality,
        "filter_mode": "SINGLE_ID_HARDWARE",
        "rx_queue_depth": 64,
        "rx_dropped_count": 0,
        "rx_overflow_count": 0,
        "frame_count": 1,
        "frames": [
            {
                "timestamp_ns": 123_000_000,
                "timestamp_provenance": "capture_tool_timestamp",
                "source_format": "candump",
                "channel": channel,
                "direction": "Rx",
                "arbitration_id": 0x123,
                "is_extended_id": False,
                "is_remote_frame": False,
                "dlc": 8,
                "data_hex": data_hex,
            }
        ],
    }


def test_empty_production_shape_emits_no_observation():
    result = decode_capture(capture(), manifest(), vehicle_profile=PROFILE)
    assert result["observation_count"] == 0
    assert result["actuation_authority"] == "NONE"


def test_semantic_candidate_decodes_offline_and_preserves_provenance():
    result = decode_capture(capture(), manifest(signal()), vehicle_profile=PROFILE)
    observation = result["observations"][0]
    assert observation["raw_value"] == 0x1234
    assert observation["value"] == pytest.approx(466.0)
    assert observation["capture_id"] == "fixture-capture"
    assert observation["timing_provenance"] == "capture_tool_timestamp"
    assert observation["decoder_status"] == "SEMANTIC_CANDIDATE"
    assert observation["capture_quality"] == "FULL_RATE_CANDIDATE"
    assert observation["observation_confidence"] == "DECODE_REVIEW_CANDIDATE"
    assert observation["actuation_authority"] == "NONE"


def test_lossy_capture_can_be_inspected_but_is_never_promoted():
    result = decode_capture(capture(quality="LOSSY"), manifest(signal()), vehicle_profile=PROFILE)
    observation = result["observations"][0]
    assert observation["value"] == pytest.approx(466.0)
    assert observation["observation_confidence"] == "LOSSY_CAPTURE_ONLY"
    assert observation["actuation_authority"] == "NONE"


def test_full_rate_candidate_rejects_observed_overflow():
    candidate_capture = capture()
    candidate_capture["rx_overflow_count"] = 1
    with pytest.raises(OfflineDecodeError, match="drops or overflows"):
        decode_capture(candidate_capture, manifest(), vehicle_profile=PROFILE)


def test_unverified_decoder_is_not_executable():
    result = decode_capture(capture(), manifest(signal("UNVERIFIED")), vehicle_profile=PROFILE)
    assert result["executable_decoder_count"] == 0
    assert result["observation_count"] == 0


def test_invalid_raw_becomes_none_and_never_zero():
    result = decode_capture(capture("00FFFF0000000000"), manifest(signal()), vehicle_profile=PROFILE)
    observation = result["observations"][0]
    assert observation["validity"] == "INVALID_RAW"
    assert observation["value"] is None


def test_out_of_range_becomes_none():
    candidate = signal()
    candidate["validity"]["physical_max"] = 10.0
    result = decode_capture(capture(), manifest(candidate), vehicle_profile=PROFILE)
    observation = result["observations"][0]
    assert observation["validity"] == "OUT_OF_RANGE"
    assert observation["value"] is None


def test_channel_mismatch_does_not_decode():
    result = decode_capture(capture(channel="can1"), manifest(signal()), vehicle_profile=PROFILE)
    assert result["observation_count"] == 0


def test_non_byte_aligned_multibyte_layout_fails_closed():
    candidate = signal()
    candidate["layout"].update({"start_byte": 1, "start_bit_in_byte": 1, "absolute_start_bit": 9, "bit_length": 12})
    with pytest.raises(OfflineDecodeError, match="fixture-backed semantics"):
        decode_capture(capture(), manifest(candidate), vehicle_profile=PROFILE)


def test_frame_count_mismatch_is_rejected():
    candidate_capture = capture()
    candidate_capture["frame_count"] = 2
    with pytest.raises(OfflineDecodeError, match="frame_count"):
        decode_capture(candidate_capture, manifest(), vehicle_profile=PROFILE)


def test_unknown_vehicle_profile_is_rejected():
    with pytest.raises(OfflineDecodeError, match="unknown vehicle profile"):
        decode_capture(capture(), manifest(), vehicle_profile="other-profile")


def test_rejected_decoder_remains_non_executable():
    rejected = signal("REJECTED")
    result = decode_capture(capture(), manifest(rejected), vehicle_profile=PROFILE)
    assert result["observation_count"] == 0


def test_state_source_candidate_still_has_no_actuation_authority():
    candidate = signal("STATE_SOURCE_CANDIDATE")
    candidate["evidence"] = [
        evidence("recorded_capture", "capture-a", "passive_can"),
        evidence("independent_sensor", "capture-b", "independent_imu"),
        evidence("cross_source_report", "report-a", "validation_report"),
    ]
    result = decode_capture(capture(), manifest(candidate), vehicle_profile=PROFILE)
    observation = result["observations"][0]
    assert observation["observation_confidence"] == "STATE_SOURCE_REVIEW_CANDIDATE"
    assert observation["actuation_authority"] == "NONE"
    assert result["actuation_authority"] == "NONE"


def test_input_manifest_validation_runs_before_decode():
    candidate = signal()
    candidate["guessed_scale"] = True
    with pytest.raises(Exception, match="guessed_scale"):
        decode_capture(capture(), manifest(candidate), vehicle_profile=PROFILE)
