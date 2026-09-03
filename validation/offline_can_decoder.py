from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from validation.bmw_decoder_manifest import validate_manifest
from validation.can_trace_compare import CanTraceComparisonReport
from validation.capture_quality_evaluator import evaluate_can_capture


EXECUTABLE_STATUSES = {
    "SEMANTIC_CANDIDATE",
    "CROSS_SOURCE_VALIDATED",
    "STATE_SOURCE_CANDIDATE",
}
CAPTURE_QUALITIES = {"UNKNOWN", "LOSSY", "OBSERVATION_ONLY", "FULL_RATE_CANDIDATE"}


class OfflineDecodeError(ValueError):
    pass


def _fail(message: str) -> None:
    raise OfflineDecodeError(message)


def _validate_capture(capture: dict[str, Any]) -> None:
    required = {
        "schema_version", "capture_id", "mode", "clock_domain", "adapter",
        "listen_only", "capture_quality", "filter_mode", "rx_queue_depth",
        "rx_dropped_count", "rx_overflow_count", "frame_count", "frames",
    }
    if not isinstance(capture, dict):
        _fail("capture must be an object")
    missing = sorted(required - set(capture))
    unknown = sorted(set(capture) - required)
    if missing:
        _fail(f"capture missing required fields: {', '.join(missing)}")
    if unknown:
        _fail(f"capture contains unknown fields: {', '.join(unknown)}")
    if capture["schema_version"] != 2:
        _fail("capture schema_version must equal 2")
    if capture["mode"] != "read_only_can_capture_import":
        _fail("capture mode must be 'read_only_can_capture_import'")
    if not isinstance(capture["frames"], list):
        _fail("capture.frames must be an array")
    if capture["frame_count"] != len(capture["frames"]):
        _fail("capture.frame_count does not match frames length")
    if capture["listen_only"] not in (True, False, None):
        _fail("capture.listen_only must be true, false or null")
    if capture["capture_quality"] not in CAPTURE_QUALITIES:
        _fail("capture.capture_quality is unsupported")
    for name in ("rx_queue_depth", "rx_dropped_count", "rx_overflow_count"):
        value = capture[name]
        if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value < 0):
            _fail(f"capture.{name} must be a non-negative integer or null")
    if capture["capture_quality"] == "FULL_RATE_CANDIDATE":
        if capture["rx_dropped_count"] not in (0, None) or capture["rx_overflow_count"] not in (0, None):
            _fail("FULL_RATE_CANDIDATE capture cannot report observed drops or overflows")


def _payload(frame: dict[str, Any]) -> bytes:
    try:
        data_hex = frame["data_hex"]
        dlc = frame["dlc"]
    except KeyError as exc:
        _fail(f"frame missing field: {exc.args[0]}")
    if not isinstance(data_hex, str) or len(data_hex) % 2:
        _fail("frame.data_hex must be even-length hexadecimal text")
    try:
        payload = bytes.fromhex(data_hex)
    except ValueError:
        _fail("frame.data_hex is not valid hexadecimal")
    if not isinstance(dlc, int) or isinstance(dlc, bool) or dlc != len(payload):
        _fail("frame DLC/data mismatch")
    return payload


def _extract_raw(payload: bytes, layout: dict[str, Any]) -> int:
    start_bit = layout["absolute_start_bit"]
    bit_length = layout["bit_length"]
    signed = layout["signed"]
    numbering = layout["bit_numbering"]
    byte_order = layout["byte_order"]

    # Multi-byte non-byte-aligned Motorola/Intel semantics are intentionally
    # not guessed. Add only with representative fixtures and schema semantics.
    if start_bit % 8 == 0 and bit_length % 8 == 0 and numbering == "lsb0":
        start = start_bit // 8
        width = bit_length // 8
        return int.from_bytes(
            payload[start:start + width],
            byteorder="little" if byte_order == "little_endian" else "big",
            signed=signed,
        )

    if bit_length <= 8 and start_bit // 8 == (start_bit + bit_length - 1) // 8:
        byte_index = start_bit // 8
        in_byte = start_bit % 8
        if numbering == "lsb0":
            shift = in_byte
        elif numbering == "msb0":
            shift = 8 - in_byte - bit_length
            if shift < 0:
                _fail("single-byte msb0 field exceeds byte boundary")
        else:
            _fail(f"unsupported bit numbering: {numbering}")
        raw = (payload[byte_index] >> shift) & ((1 << bit_length) - 1)
        if signed and raw & (1 << (bit_length - 1)):
            raw -= 1 << bit_length
        return raw

    _fail(
        "layout is not executable yet: non-byte-aligned multi-byte fields "
        "require fixture-backed semantics"
    )


def _decoder_matches_frame(signal: dict[str, Any], frame: dict[str, Any]) -> bool:
    selector = signal["frame"]
    return (
        frame.get("direction") == "Rx"
        and frame.get("channel") == signal["channel"]
        and frame.get("arbitration_id") == selector["arbitration_id"]
        and frame.get("is_extended_id") == selector["is_extended_id"]
        and frame.get("dlc") == selector["dlc"]
    )


def _decode_value(raw: int, signal: dict[str, Any]) -> tuple[Any, str]:
    validity = signal["validity"]
    if raw in validity["invalid_raw_values"]:
        return None, "INVALID_RAW"

    choices = signal["conversion"]["choices"]
    if str(raw) in choices:
        value: Any = choices[str(raw)]
    else:
        value = raw * signal["conversion"]["scale"] + signal["conversion"]["offset"]

    physical_min = validity["physical_min"]
    physical_max = validity["physical_max"]
    if isinstance(value, (int, float)) and physical_min is not None:
        if value < physical_min or value > physical_max:
            return None, "OUT_OF_RANGE"
    return value, "VALID"


def _observation_confidence(capture_quality: str, decoder_status: str) -> str:
    if capture_quality == "LOSSY":
        return "LOSSY_CAPTURE_ONLY"
    if capture_quality in {"UNKNOWN", "OBSERVATION_ONLY"}:
        return "OBSERVATION_ONLY"
    if decoder_status == "STATE_SOURCE_CANDIDATE":
        return "STATE_SOURCE_REVIEW_CANDIDATE"
    return "DECODE_REVIEW_CANDIDATE"


def decode_capture(
    capture: dict[str, Any],
    manifest: dict[str, Any],
    *,
    vehicle_profile: str,
    reference_comparison: CanTraceComparisonReport | None = None,
) -> dict[str, Any]:
    _validate_capture(capture)
    quality_report = evaluate_can_capture(
        capture, reference_comparison=reference_comparison
    )
    evaluated_capture_quality = quality_report.evaluated_quality
    manifest_report = validate_manifest(manifest)
    profiles = manifest["vehicle_profiles"]
    if vehicle_profile not in profiles:
        _fail(f"unknown vehicle profile: {vehicle_profile}")

    decoders = [
        signal
        for signal in manifest["signals"]
        if signal["validation_status"] in EXECUTABLE_STATUSES
        and vehicle_profile in signal["vehicle_applicability"]["profile_ids"]
    ]

    observations: list[dict[str, Any]] = []
    for frame_index, frame in enumerate(capture["frames"]):
        payload = _payload(frame)
        for signal in decoders:
            if not _decoder_matches_frame(signal, frame):
                continue
            raw = _extract_raw(payload, signal["layout"])
            value, validity = _decode_value(raw, signal)
            observations.append(
                {
                    "capture_id": capture["capture_id"],
                    "frame_index": frame_index,
                    "sample_time_ns": frame["timestamp_ns"],
                    "receive_time_ns": frame["timestamp_ns"],
                    "clock_domain": capture["clock_domain"],
                    "timing_provenance": frame["timestamp_provenance"],
                    "adapter": capture["adapter"],
                    "listen_only": capture["listen_only"],
                    "declared_capture_quality": capture["capture_quality"],
                    "capture_quality": evaluated_capture_quality,
                    "filter_mode": capture["filter_mode"],
                    "rx_queue_depth": capture["rx_queue_depth"],
                    "rx_dropped_count": capture["rx_dropped_count"],
                    "rx_overflow_count": capture["rx_overflow_count"],
                    "source_format": frame["source_format"],
                    "source_channel": frame["channel"],
                    "decoder_id": signal["decoder_id"],
                    "decoder_version": signal["decoder_version"],
                    "decoder_status": signal["validation_status"],
                    "observation_confidence": _observation_confidence(
                        evaluated_capture_quality, signal["validation_status"]
                    ),
                    "signal": signal["signal"],
                    "state_path": signal["state_path"],
                    "raw_value": raw,
                    "value": value,
                    "unit": signal["conversion"]["unit"],
                    "validity": validity,
                    "stale_after_ns": signal["validity"]["stale_after_ns"],
                    "actuation_authority": "NONE",
                }
            )

    return {
        "schema_version": 2,
        "mode": "offline_manifest_can_decode",
        "capture_id": capture["capture_id"],
        "declared_capture_quality": capture["capture_quality"],
        "capture_quality": evaluated_capture_quality,
        "capture_quality_evaluation": quality_report.to_dict(),
        "vehicle_profile": vehicle_profile,
        "manifest_id": manifest_report["manifest_id"],
        "manifest_signal_count": manifest_report["signal_count"],
        "executable_decoder_count": len(decoders),
        "observation_count": len(observations),
        "observations": observations,
        "actuation_authority": "NONE",
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Decode canonical CAN captures offline through an evidence-gated manifest"
    )
    parser.add_argument("capture", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--vehicle-profile", required=True)
    parser.add_argument("--reference-comparison", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    capture = json.loads(args.capture.read_text(encoding="utf-8"))
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    comparison = (
        None
        if args.reference_comparison is None
        else CanTraceComparisonReport.from_dict(
            json.loads(args.reference_comparison.read_text(encoding="utf-8"))
        )
    )
    result = decode_capture(
        capture,
        manifest,
        vehicle_profile=args.vehicle_profile,
        reference_comparison=comparison,
    )
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
