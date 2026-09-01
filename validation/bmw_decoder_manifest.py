from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any


MANIFEST_SCHEMA_VERSION = 1
MANIFEST_MODE = "read_only_decoder_manifest"

VALIDATION_STATUSES = {
    "UNVERIFIED",
    "FRAME_OBSERVED",
    "SEMANTIC_CANDIDATE",
    "CROSS_SOURCE_VALIDATED",
    "STATE_SOURCE_CANDIDATE",
    "REJECTED",
}

EVIDENCE_KINDS = {
    "official_documentation",
    "recorded_capture",
    "cluster_observation",
    "diagnostic_read_only",
    "independent_sensor",
    "cross_source_report",
    "community_reference",
}

BMW_STATE_GROUPS = {
    "chassis",
    "powertrain",
    "adas",
    "parking",
    "body",
    "driver",
    "environment",
    "energy",
    "health",
}

_IDENTIFIER_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_SIGNAL_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_STATE_PATH_RE = re.compile(r"^[a-z][A-Za-z0-9]*(?:\.[A-Za-z][A-Za-z0-9]*)+$")
_SEMVER_RE = re.compile(r"^(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_INTEGER_TEXT_RE = re.compile(r"^-?(?:0|[1-9]\d*)$")
_PLACEHOLDERS = {"UNKNOWN", "UNSPECIFIED", "TBD", "TODO"}


class ManifestValidationError(ValueError):
    """Raised when a decoder manifest is ambiguous or unsafe to consume."""


def _fail(path: str, message: str) -> None:
    raise ManifestValidationError(f"{path}: {message}")


def _mapping(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail(path, "must be an object")
    return value


def _list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        _fail(path, "must be an array")
    return value


def _exact_keys(
    value: dict[str, Any],
    *,
    required: set[str],
    path: str,
) -> None:
    missing = sorted(required - set(value))
    unknown = sorted(set(value) - required)
    if missing:
        _fail(path, f"missing required fields: {', '.join(missing)}")
    if unknown:
        _fail(path, f"unknown fields: {', '.join(unknown)}")


def _nonempty_string(value: Any, path: str, *, allow_placeholder: bool = False) -> str:
    if not isinstance(value, str) or not value.strip():
        _fail(path, "must be a non-empty string")
    result = value.strip()
    if not allow_placeholder and result.upper() in _PLACEHOLDERS:
        _fail(path, "must not use an unknown/TBD placeholder")
    return result


def _integer(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        _fail(path, "must be an integer")
    return value


def _optional_integer(value: Any, path: str) -> int | None:
    if value is None:
        return None
    return _integer(value, path)


def _finite_number(value: Any, path: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _fail(path, "must be a number")
    result = float(value)
    if not math.isfinite(result):
        _fail(path, "must be finite")
    return result


def _optional_number(value: Any, path: str) -> float | None:
    if value is None:
        return None
    return _finite_number(value, path)


def _unique_string_list(value: Any, path: str, *, nonempty: bool = False) -> list[str]:
    values = _list(value, path)
    if nonempty and not values:
        _fail(path, "must contain at least one value")
    result = [_nonempty_string(item, f"{path}[{index}]", allow_placeholder=True) for index, item in enumerate(values)]
    if len(result) != len(set(result)):
        _fail(path, "must not contain duplicate values")
    return result


def _validate_profile(profile_id: str, raw: Any) -> None:
    path = f"vehicle_profiles.{profile_id}"
    if not _IDENTIFIER_RE.fullmatch(profile_id):
        _fail(path, "profile ID must use lowercase letters, digits, '.', '_' or '-'")

    profile = _mapping(raw, path)
    _exact_keys(
        profile,
        required={"make", "chassis", "model", "model_year", "powertrain", "notes"},
        path=path,
    )
    for field in ("make", "chassis", "model", "powertrain"):
        _nonempty_string(profile[field], f"{path}.{field}")
    model_year = _integer(profile["model_year"], f"{path}.model_year")
    if not 1980 <= model_year <= 2100:
        _fail(f"{path}.model_year", "must be between 1980 and 2100")
    if not isinstance(profile["notes"], str):
        _fail(f"{path}.notes", "must be a string")


def _validate_frame(raw: Any, path: str) -> dict[str, Any]:
    frame = _mapping(raw, path)
    _exact_keys(
        frame,
        required={"arbitration_id", "is_extended_id", "dlc", "direction"},
        path=path,
    )

    arbitration_id = _integer(frame["arbitration_id"], f"{path}.arbitration_id")
    if not 0 <= arbitration_id <= 0x1FFFFFFF:
        _fail(f"{path}.arbitration_id", "must fit a 29-bit CAN identifier")

    if not isinstance(frame["is_extended_id"], bool):
        _fail(f"{path}.is_extended_id", "must be a boolean")
    if not frame["is_extended_id"] and arbitration_id > 0x7FF:
        _fail(f"{path}.arbitration_id", "standard CAN identifiers must be <= 0x7FF")

    dlc = _integer(frame["dlc"], f"{path}.dlc")
    if not 1 <= dlc <= 8:
        _fail(f"{path}.dlc", "initial manifest supports classic CAN DLC 1..8 only")

    if frame["direction"] != "Rx":
        _fail(f"{path}.direction", "must be 'Rx' at the read-only decoder boundary")
    return frame


def _validate_layout(raw: Any, path: str, *, dlc: int) -> dict[str, Any]:
    layout = _mapping(raw, path)
    _exact_keys(
        layout,
        required={
            "start_byte",
            "start_bit_in_byte",
            "absolute_start_bit",
            "bit_length",
            "bit_numbering",
            "byte_order",
            "signed",
        },
        path=path,
    )

    start_byte = _integer(layout["start_byte"], f"{path}.start_byte")
    start_bit_in_byte = _integer(layout["start_bit_in_byte"], f"{path}.start_bit_in_byte")
    absolute_start_bit = _integer(layout["absolute_start_bit"], f"{path}.absolute_start_bit")
    bit_length = _integer(layout["bit_length"], f"{path}.bit_length")

    if start_byte < 0:
        _fail(f"{path}.start_byte", "must be >= 0")
    if not 0 <= start_bit_in_byte <= 7:
        _fail(f"{path}.start_bit_in_byte", "must be between 0 and 7")
    if absolute_start_bit != start_byte * 8 + start_bit_in_byte:
        _fail(path, "absolute_start_bit must equal start_byte * 8 + start_bit_in_byte")
    if bit_length <= 0:
        _fail(f"{path}.bit_length", "must be > 0")
    if absolute_start_bit + bit_length > dlc * 8:
        _fail(path, "signal bit range exceeds the declared DLC")

    if layout["bit_numbering"] not in {"lsb0", "msb0"}:
        _fail(f"{path}.bit_numbering", "must be 'lsb0' or 'msb0'")
    if layout["byte_order"] not in {"little_endian", "big_endian"}:
        _fail(f"{path}.byte_order", "must be 'little_endian' or 'big_endian'")
    if not isinstance(layout["signed"], bool):
        _fail(f"{path}.signed", "must be a boolean")
    return layout


def _validate_conversion(raw: Any, path: str) -> None:
    conversion = _mapping(raw, path)
    _exact_keys(conversion, required={"scale", "offset", "unit", "choices"}, path=path)
    scale = _finite_number(conversion["scale"], f"{path}.scale")
    if scale == 0.0:
        _fail(f"{path}.scale", "must not be zero")
    _finite_number(conversion["offset"], f"{path}.offset")
    _nonempty_string(conversion["unit"], f"{path}.unit")

    choices = _mapping(conversion["choices"], f"{path}.choices")
    for raw_value, label in choices.items():
        if not isinstance(raw_value, str) or not _INTEGER_TEXT_RE.fullmatch(raw_value):
            _fail(f"{path}.choices", "choice keys must be canonical integer strings")
        _nonempty_string(label, f"{path}.choices[{raw_value!r}]")


def _raw_range(bit_length: int, signed: bool) -> tuple[int, int]:
    if signed:
        return -(1 << (bit_length - 1)), (1 << (bit_length - 1)) - 1
    return 0, (1 << bit_length) - 1


def _validate_validity(raw: Any, path: str, *, bit_length: int, signed: bool) -> dict[str, Any]:
    validity = _mapping(raw, path)
    _exact_keys(
        validity,
        required={"physical_min", "physical_max", "stale_after_ns", "invalid_raw_values"},
        path=path,
    )

    physical_min = _optional_number(validity["physical_min"], f"{path}.physical_min")
    physical_max = _optional_number(validity["physical_max"], f"{path}.physical_max")
    if (physical_min is None) != (physical_max is None):
        _fail(path, "physical_min and physical_max must both be known or both be null")
    if physical_min is not None and physical_max is not None and physical_min >= physical_max:
        _fail(path, "physical_min must be less than physical_max")

    stale_after_ns = _optional_integer(validity["stale_after_ns"], f"{path}.stale_after_ns")
    if stale_after_ns is not None and stale_after_ns <= 0:
        _fail(f"{path}.stale_after_ns", "must be > 0 when specified")

    invalid_values = _list(validity["invalid_raw_values"], f"{path}.invalid_raw_values")
    checked_values = [
        _integer(value, f"{path}.invalid_raw_values[{index}]")
        for index, value in enumerate(invalid_values)
    ]
    if len(checked_values) != len(set(checked_values)):
        _fail(f"{path}.invalid_raw_values", "must not contain duplicates")
    raw_min, raw_max = _raw_range(bit_length, signed)
    for value in checked_values:
        if not raw_min <= value <= raw_max:
            _fail(
                f"{path}.invalid_raw_values",
                f"value {value} does not fit the declared {bit_length}-bit field",
            )
    return validity


def _validate_evidence(raw: Any, path: str) -> list[dict[str, Any]]:
    evidence = _list(raw, path)
    if not evidence:
        _fail(path, "a manifest entry must cite at least one evidence item")

    result: list[dict[str, Any]] = []
    identities: set[tuple[str, str, str | None]] = set()
    for index, item_raw in enumerate(evidence):
        item_path = f"{path}[{index}]"
        item = _mapping(item_raw, item_path)
        _exact_keys(
            item,
            required={"kind", "reference", "independence_group", "capture_id", "sha256", "notes"},
            path=item_path,
        )
        if item["kind"] not in EVIDENCE_KINDS:
            _fail(f"{item_path}.kind", f"unsupported evidence kind: {item['kind']!r}")
        reference = _nonempty_string(item["reference"], f"{item_path}.reference")
        independence_group = _nonempty_string(
            item["independence_group"], f"{item_path}.independence_group"
        )
        capture_id = item["capture_id"]
        if capture_id is not None:
            capture_id = _nonempty_string(capture_id, f"{item_path}.capture_id")
        sha256 = item["sha256"]
        if sha256 is not None:
            if not isinstance(sha256, str) or not _SHA256_RE.fullmatch(sha256):
                _fail(f"{item_path}.sha256", "must be 64 lowercase hexadecimal characters or null")
        if not isinstance(item["notes"], str):
            _fail(f"{item_path}.notes", "must be a string")

        identity = (item["kind"], reference, capture_id)
        if identity in identities:
            _fail(item_path, "duplicates an earlier evidence item")
        identities.add(identity)
        result.append({**item, "independence_group": independence_group})
    return result


def _validate_applicability(raw: Any, path: str, *, profile_ids: set[str]) -> list[str]:
    applicability = _mapping(raw, path)
    _exact_keys(
        applicability,
        required={"profile_ids", "ecu_part_numbers", "software_versions", "notes"},
        path=path,
    )
    referenced_profiles = _unique_string_list(
        applicability["profile_ids"], f"{path}.profile_ids", nonempty=True
    )
    unknown_profiles = sorted(set(referenced_profiles) - profile_ids)
    if unknown_profiles:
        _fail(f"{path}.profile_ids", f"unknown profiles: {', '.join(unknown_profiles)}")
    _unique_string_list(applicability["ecu_part_numbers"], f"{path}.ecu_part_numbers")
    _unique_string_list(applicability["software_versions"], f"{path}.software_versions")
    if not isinstance(applicability["notes"], str):
        _fail(f"{path}.notes", "must be a string")
    return referenced_profiles


def _validate_signal(raw: Any, index: int, *, profile_ids: set[str]) -> dict[str, Any]:
    path = f"signals[{index}]"
    signal = _mapping(raw, path)
    _exact_keys(
        signal,
        required={
            "decoder_id",
            "signal",
            "state_path",
            "transport",
            "bus",
            "channel",
            "frame",
            "layout",
            "conversion",
            "validity",
            "evidence",
            "vehicle_applicability",
            "decoder_version",
            "validation_status",
            "notes",
        },
        path=path,
    )

    decoder_id = _nonempty_string(signal["decoder_id"], f"{path}.decoder_id")
    if not _IDENTIFIER_RE.fullmatch(decoder_id):
        _fail(f"{path}.decoder_id", "must use lowercase letters, digits, '.', '_' or '-'")

    semantic_name = _nonempty_string(signal["signal"], f"{path}.signal")
    if not _SIGNAL_RE.fullmatch(semantic_name):
        _fail(f"{path}.signal", "must be a lowercase snake_case semantic name")

    state_path = _nonempty_string(signal["state_path"], f"{path}.state_path")
    if not _STATE_PATH_RE.fullmatch(state_path):
        _fail(f"{path}.state_path", "must be a dotted BMWVehicleState path")
    group = state_path.split(".", 1)[0]
    if group not in BMW_STATE_GROUPS:
        _fail(f"{path}.state_path", f"unsupported BMWVehicleState group: {group}")

    if signal["transport"] != "CAN":
        _fail(f"{path}.transport", "initial decoder manifest supports 'CAN' only")
    bus = _nonempty_string(signal["bus"], f"{path}.bus")
    channel = _nonempty_string(signal["channel"], f"{path}.channel")

    frame = _validate_frame(signal["frame"], f"{path}.frame")
    layout = _validate_layout(signal["layout"], f"{path}.layout", dlc=frame["dlc"])
    _validate_conversion(signal["conversion"], f"{path}.conversion")
    validity = _validate_validity(
        signal["validity"],
        f"{path}.validity",
        bit_length=layout["bit_length"],
        signed=layout["signed"],
    )
    evidence = _validate_evidence(signal["evidence"], f"{path}.evidence")
    applicable_profiles = _validate_applicability(
        signal["vehicle_applicability"],
        f"{path}.vehicle_applicability",
        profile_ids=profile_ids,
    )

    decoder_version = _nonempty_string(signal["decoder_version"], f"{path}.decoder_version")
    if not _SEMVER_RE.fullmatch(decoder_version):
        _fail(f"{path}.decoder_version", "must be a three-part semantic version such as 0.1.0")

    status = signal["validation_status"]
    if status not in VALIDATION_STATUSES:
        _fail(f"{path}.validation_status", f"unsupported status: {status!r}")

    if status in {"CROSS_SOURCE_VALIDATED", "STATE_SOURCE_CANDIDATE"}:
        source_groups = {
            item["independence_group"]
            for item in evidence
            if item["kind"] != "cross_source_report"
        }
        if len(source_groups) < 2:
            _fail(path, f"{status} requires evidence from at least two independent source groups")
        if not any(item["kind"] == "cross_source_report" for item in evidence):
            _fail(path, f"{status} requires a cross_source_report evidence item")

    if status == "STATE_SOURCE_CANDIDATE":
        if validity["physical_min"] is None or validity["physical_max"] is None:
            _fail(path, "STATE_SOURCE_CANDIDATE requires a known physical validity range")
        if validity["stale_after_ns"] is None:
            _fail(path, "STATE_SOURCE_CANDIDATE requires a stale_after_ns policy")

    if not isinstance(signal["notes"], str):
        _fail(f"{path}.notes", "must be a string")

    return {
        "decoder_id": decoder_id,
        "semantic_name": semantic_name,
        "state_path": state_path,
        "decoder_version": decoder_version,
        "validation_status": status,
        "applicable_profiles": applicable_profiles,
        "selector": (
            signal["transport"],
            bus,
            channel,
            frame["arbitration_id"],
            frame["is_extended_id"],
            layout["absolute_start_bit"],
            layout["bit_length"],
        ),
    }


def validate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    manifest = _mapping(manifest, "manifest")
    _exact_keys(
        manifest,
        required={"schema_version", "manifest_id", "mode", "vehicle_profiles", "signals"},
        path="manifest",
    )

    if _integer(manifest["schema_version"], "schema_version") != MANIFEST_SCHEMA_VERSION:
        _fail("schema_version", f"must equal {MANIFEST_SCHEMA_VERSION}")
    manifest_id = _nonempty_string(manifest["manifest_id"], "manifest_id")
    if not _IDENTIFIER_RE.fullmatch(manifest_id):
        _fail("manifest_id", "must use lowercase letters, digits, '.', '_' or '-'")
    if manifest["mode"] != MANIFEST_MODE:
        _fail("mode", f"must equal {MANIFEST_MODE!r}")

    profiles = _mapping(manifest["vehicle_profiles"], "vehicle_profiles")
    if not profiles:
        _fail("vehicle_profiles", "must define at least one explicit vehicle profile")
    for profile_id, profile in profiles.items():
        if not isinstance(profile_id, str):
            _fail("vehicle_profiles", "profile IDs must be strings")
        _validate_profile(profile_id, profile)
    profile_ids = set(profiles)

    signals = _list(manifest["signals"], "signals")
    summaries = [
        _validate_signal(signal, index, profile_ids=profile_ids)
        for index, signal in enumerate(signals)
    ]

    decoder_ids: set[str] = set()
    selectors_by_profile: set[tuple[Any, ...]] = set()
    state_versions_by_profile: set[tuple[str, str, str]] = set()
    for index, summary in enumerate(summaries):
        if summary["decoder_id"] in decoder_ids:
            _fail(f"signals[{index}].decoder_id", "duplicates an earlier decoder_id")
        decoder_ids.add(summary["decoder_id"])

        if summary["validation_status"] == "REJECTED":
            continue
        for profile_id in summary["applicable_profiles"]:
            selector_key = (profile_id, *summary["selector"])
            if selector_key in selectors_by_profile:
                _fail(f"signals[{index}]", "duplicates an active bit selector for the same vehicle profile")
            selectors_by_profile.add(selector_key)

            state_key = (profile_id, summary["state_path"], summary["decoder_version"])
            if state_key in state_versions_by_profile:
                _fail(
                    f"signals[{index}]",
                    "duplicates an active state_path and decoder_version for the same vehicle profile",
                )
            state_versions_by_profile.add(state_key)

    status_counts = Counter(summary["validation_status"] for summary in summaries)
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "manifest_id": manifest_id,
        "mode": MANIFEST_MODE,
        "vehicle_profile_count": len(profiles),
        "signal_count": len(summaries),
        "active_signal_count": sum(
            1 for summary in summaries if summary["validation_status"] != "REJECTED"
        ),
        "state_source_candidate_count": status_counts.get("STATE_SOURCE_CANDIDATE", 0),
        "status_counts": dict(sorted(status_counts.items())),
        "actuation_authority": "NONE",
    }


def load_manifest(path: str | Path) -> tuple[dict[str, Any], dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    return manifest, validate_manifest(manifest)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate the declarative, read-only BMW observation decoder manifest"
    )
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    _, report = load_manifest(args.manifest)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
