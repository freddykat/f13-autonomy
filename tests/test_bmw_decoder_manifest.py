import copy
import json
from pathlib import Path

import pytest

from validation.bmw_decoder_manifest import ManifestValidationError, validate_manifest


MANIFEST_PATH = (
    Path(__file__).parents[1]
    / "validation"
    / "manifests"
    / "prototype_001_bmw_decoders.json"
)


def empty_manifest():
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def fixture_signal():
    # 0x123 and every semantic value below are test-fixture data, not BMW decodes.
    return {
        "decoder_id": "fixture.can.signal.v1",
        "signal": "fixture_signal",
        "state_path": "chassis.fixtureSignal",
        "transport": "CAN",
        "bus": "FIXTURE_BUS",
        "channel": "fixture0",
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
            "physical_min": None,
            "physical_max": None,
            "stale_after_ns": None,
            "invalid_raw_values": [65535],
        },
        "evidence": [
            {
                "kind": "community_reference",
                "reference": "tests/fixtures/not-a-real-bmw-decode",
                "independence_group": "fixture_only",
                "capture_id": None,
                "sha256": None,
                "notes": "Synthetic validator fixture.",
            }
        ],
        "vehicle_applicability": {
            "profile_ids": ["prototype-001-f13-650i-xdrive-2012"],
            "ecu_part_numbers": [],
            "software_versions": [],
            "notes": "Synthetic validator fixture only.",
        },
        "decoder_version": "0.1.0",
        "validation_status": "UNVERIFIED",
        "notes": "Synthetic validator fixture; never add this to the production manifest.",
    }


def manifest_with_signal(signal=None):
    manifest = empty_manifest()
    manifest["signals"] = [signal or fixture_signal()]
    return manifest


def evidence(kind, reference, independence_group):
    return {
        "kind": kind,
        "reference": reference,
        "independence_group": independence_group,
        "capture_id": None,
        "sha256": None,
        "notes": "Synthetic test evidence.",
    }


def test_committed_manifest_is_valid_and_contains_no_unconfirmed_signals():
    report = validate_manifest(empty_manifest())
    assert report["signal_count"] == 0
    assert report["state_source_candidate_count"] == 0
    assert report["actuation_authority"] == "NONE"


def test_complete_unverified_fixture_entry_is_accepted_without_promotion():
    report = validate_manifest(manifest_with_signal())
    assert report["signal_count"] == 1
    assert report["status_counts"] == {"UNVERIFIED": 1}
    assert report["state_source_candidate_count"] == 0


def test_unknown_fields_are_rejected_instead_of_silently_ignored():
    signal = fixture_signal()
    signal["guessed_scale"] = True
    with pytest.raises(ManifestValidationError, match="unknown fields: guessed_scale"):
        validate_manifest(manifest_with_signal(signal))


def test_standard_can_identifier_must_fit_eleven_bits():
    signal = fixture_signal()
    signal["frame"]["arbitration_id"] = 0x1800
    with pytest.raises(ManifestValidationError, match="standard CAN identifiers"):
        validate_manifest(manifest_with_signal(signal))


def test_start_byte_and_absolute_bit_must_agree():
    signal = fixture_signal()
    signal["layout"]["absolute_start_bit"] = 7
    with pytest.raises(ManifestValidationError, match="absolute_start_bit must equal"):
        validate_manifest(manifest_with_signal(signal))


def test_bit_range_must_fit_declared_dlc():
    signal = fixture_signal()
    signal["layout"].update(
        {
            "start_byte": 7,
            "start_bit_in_byte": 0,
            "absolute_start_bit": 56,
            "bit_length": 16,
        }
    )
    with pytest.raises(ManifestValidationError, match="exceeds the declared DLC"):
        validate_manifest(manifest_with_signal(signal))


def test_tx_selector_is_rejected_at_read_only_boundary():
    signal = fixture_signal()
    signal["frame"]["direction"] = "Tx"
    with pytest.raises(ManifestValidationError, match="read-only decoder boundary"):
        validate_manifest(manifest_with_signal(signal))


def test_signal_must_reference_a_known_vehicle_profile():
    signal = fixture_signal()
    signal["vehicle_applicability"]["profile_ids"] = ["unknown-f13"]
    with pytest.raises(ManifestValidationError, match="unknown profiles"):
        validate_manifest(manifest_with_signal(signal))


def test_cross_source_status_requires_two_sources_and_a_report():
    signal = fixture_signal()
    signal["validation_status"] = "CROSS_SOURCE_VALIDATED"
    signal["evidence"] = [
        evidence("recorded_capture", "capture-a", "passive_can"),
        evidence("independent_sensor", "capture-b", "independent_imu"),
    ]
    with pytest.raises(ManifestValidationError, match="requires a cross_source_report"):
        validate_manifest(manifest_with_signal(signal))


def test_state_source_candidate_requires_validity_and_stale_policy():
    signal = fixture_signal()
    signal["validation_status"] = "STATE_SOURCE_CANDIDATE"
    signal["evidence"] = [
        evidence("recorded_capture", "capture-a", "passive_can"),
        evidence("independent_sensor", "capture-b", "independent_imu"),
        evidence("cross_source_report", "report-a", "validation_report"),
    ]
    with pytest.raises(ManifestValidationError, match="known physical validity range"):
        validate_manifest(manifest_with_signal(signal))


def test_fully_evidenced_state_source_candidate_is_eligible_for_review_only():
    signal = fixture_signal()
    signal["validation_status"] = "STATE_SOURCE_CANDIDATE"
    signal["validity"] = {
        "physical_min": -10.0,
        "physical_max": 100.0,
        "stale_after_ns": 100_000_000,
        "invalid_raw_values": [65535],
    }
    signal["evidence"] = [
        evidence("recorded_capture", "capture-a", "passive_can"),
        evidence("independent_sensor", "capture-b", "independent_imu"),
        evidence("cross_source_report", "report-a", "validation_report"),
    ]
    report = validate_manifest(manifest_with_signal(signal))
    assert report["state_source_candidate_count"] == 1
    assert report["actuation_authority"] == "NONE"


def test_duplicate_decoder_ids_are_rejected():
    first = fixture_signal()
    second = copy.deepcopy(first)
    second["layout"].update(
        {
            "start_byte": 4,
            "start_bit_in_byte": 0,
            "absolute_start_bit": 32,
        }
    )
    manifest = empty_manifest()
    manifest["signals"] = [first, second]
    with pytest.raises(ManifestValidationError, match="duplicates an earlier decoder_id"):
        validate_manifest(manifest)
