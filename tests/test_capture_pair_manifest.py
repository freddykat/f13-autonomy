import pytest

from validation.capture_pair_manifest import (
    CapturePairManifest,
    CapturePairManifestError,
    build_capture_pair_manifest,
    capture_document_sha256,
)


def capture(capture_id, payloads, *, reference_quality=False):
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
                "timestamp_ns": 100 + index * 100,
                "timestamp_provenance": "capture_tool_timestamp",
                "source_format": "fixture",
                "channel": "can0",
                "direction": "Rx",
                "arbitration_id": 0x123,
                "is_extended_id": False,
                "is_remote_frame": False,
                "dlc": 1,
                "data_hex": payload,
            }
            for index, payload in enumerate(payloads)
        ],
    }


def manifest(reference, candidate, *, method="OBSERVED_MARKER"):
    return build_capture_pair_manifest(
        reference,
        candidate,
        pair_id="pair-001",
        session_id="f13-session-001",
        logical_bus="PT-CAN-observation",
        physical_tap="gateway breakout receive-only",
        same_physical_interval=True,
        sync_method=method,
        sync_evidence="shared ignition transition marker",
    )


def test_manifest_binds_ids_and_canonical_document_hashes():
    reference = capture("vector-ref", ["01"], reference_quality=True)
    candidate = capture("panda-candidate", ["01"])
    result = manifest(reference, candidate)
    assert result.reference_document_sha256 == capture_document_sha256(reference)
    assert result.candidate_document_sha256 == capture_document_sha256(candidate)
    assert result.sync_quality == "VERIFIED"
    assert result.actuation_authority == "NONE"


def test_manifest_round_trips_through_strict_json_contract():
    reference = capture("ref", ["01"], reference_quality=True)
    candidate = capture("candidate", ["01"])
    original = manifest(reference, candidate)
    assert CapturePairManifest.from_dict(original.to_dict()) == original


def test_changed_capture_is_rejected_by_hash():
    reference = capture("ref", ["01"], reference_quality=True)
    candidate = capture("candidate", ["01"])
    result = manifest(reference, candidate)
    candidate["frames"][0]["data_hex"] = "FF"
    with pytest.raises(CapturePairManifestError, match="content hash"):
        result.validate_against(reference, candidate)


def test_shared_clock_requires_same_clock_domain():
    reference = capture("ref", ["01"], reference_quality=True)
    candidate = capture("candidate", ["01"])
    with pytest.raises(CapturePairManifestError, match="equal capture clock_domain"):
        manifest(reference, candidate, method="SHARED_CLOCK")


def test_manual_assertion_remains_declared_only():
    reference = capture("ref", ["01"], reference_quality=True)
    candidate = capture("candidate", ["01"])
    result = manifest(reference, candidate, method="MANUAL_ASSERTION")
    assert result.sync_quality == "DECLARED_ONLY"


def test_manifest_never_accepts_actuation_authority():
    reference = capture("ref", ["01"], reference_quality=True)
    candidate = capture("candidate", ["01"])
    raw = manifest(reference, candidate).to_dict()
    raw["actuation_authority"] = "CAN_TX"
    with pytest.raises(CapturePairManifestError, match="cannot grant actuation"):
        CapturePairManifest.from_dict(raw)
