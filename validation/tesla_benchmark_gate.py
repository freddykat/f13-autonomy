#!/usr/bin/env python3
"""Qualify Tesla HW4 observations for offline openpilot comparison.

This module intentionally contains no CAN identifiers, transmit API or vehicle
command translation.  It decides only whether an episode has enough provenance
to be compared, reviewed and retained as benchmark evidence.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


HEX_COMMIT = re.compile(r"^[0-9a-f]{40}$")
COMPARISON_MODES = {"SAME_EPISODE", "REPLAY_SAME_INPUT", "MATCHED_SCENARIO"}
ALIGNMENT_METHODS = {
    "SHARED_MONOTONIC_CLOCK",
    "PPS_SYNCHRONIZED",
    "OBSERVED_MARKER",
    "REPLAY_INPUT_TIMELINE",
    "MATCHED_SCENARIO_ONLY",
}
TRUSTED_TIMING = {"PER_FRAME_MONOTONIC", "ECU_SAMPLE_COUNTER", "PPS_DISCIPLINED"}
CAPTURE_QUALITIES = {"LOSSY", "OBSERVATION_ONLY", "FULL_RATE_CANDIDATE"}
SIGNAL_STATUSES = {"UNKNOWN", "OBSERVED", "CROSS_SOURCE_VALIDATED"}
SIGNAL_NAMES = {
    "autopilot_state",
    "desired_speed_mps",
    "longitudinal_intent",
    "lane_change_state",
    "lane_change_direction",
    "blind_spot_left",
    "blind_spot_right",
    "forward_collision_warning",
    "lead_distance_m",
    "lead_relative_speed_mps",
    "target_curvature_1pm",
}
EVIDENCE_TYPES = {
    "CAN_OBSERVATION",
    "UI_VIDEO",
    "VEHICLE_RESPONSE",
    "OPENPILOT_LOG",
    "HUMAN_REVIEW",
}


class TeslaBenchmarkError(ValueError):
    """The benchmark episode violates the read-only evidence contract."""


@dataclass(frozen=True)
class TeslaBenchmarkReport:
    schema_version: int
    episode_id: str
    comparison_mode: str
    classification: str
    comparable_signal_count: int
    cross_validated_signal_count: int
    reasons: tuple[str, ...]
    errors: tuple[str, ...]
    actuation_authority: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["reasons"] = list(self.reasons)
        data["errors"] = list(self.errors)
        return data


def _exact_keys(value: dict[str, Any], expected: set[str], location: str) -> None:
    missing = sorted(expected - set(value))
    unknown = sorted(set(value) - expected)
    if missing or unknown:
        parts = []
        if missing:
            parts.append(f"missing fields: {', '.join(missing)}")
        if unknown:
            parts.append(f"unknown fields: {', '.join(unknown)}")
        raise TeslaBenchmarkError(f"{location}: {'; '.join(parts)}")


def _object(value: Any, location: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TeslaBenchmarkError(f"{location} must be an object")
    return value


def _string(value: Any, location: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TeslaBenchmarkError(f"{location} must be a non-empty string")
    return value


def _enum(value: Any, choices: set[str], location: str) -> str:
    parsed = _string(value, location)
    if parsed not in choices:
        raise TeslaBenchmarkError(f"{location} must be one of {sorted(choices)}")
    return parsed


def _counter(value: Any, location: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise TeslaBenchmarkError(f"{location} must be null or a non-negative integer")
    return value


def _finite_number(value: Any, location: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise TeslaBenchmarkError(f"{location} must be a finite number")
    return float(value)


def _validate_openpilot(raw: Any, expected_commit: str) -> dict[str, Any]:
    data = _object(raw, "openpilot")
    _exact_keys(
        data,
        {
            "baseline_commit",
            "model_artifact",
            "capture_id",
            "clock_domain",
            "timing_provenance",
            "capture_quality",
            "camera_dropped_frame_count",
            "model_skipped_frame_count",
        },
        "openpilot",
    )
    commit = _string(data["baseline_commit"], "openpilot.baseline_commit")
    if HEX_COMMIT.fullmatch(commit) is None:
        raise TeslaBenchmarkError("openpilot.baseline_commit must be a full Git commit")
    if commit != expected_commit:
        raise TeslaBenchmarkError("openpilot.baseline_commit differs from the locked project baseline")
    for field in ("model_artifact", "capture_id", "clock_domain", "timing_provenance"):
        _string(data[field], f"openpilot.{field}")
    _enum(data["capture_quality"], CAPTURE_QUALITIES, "openpilot.capture_quality")
    _counter(data["camera_dropped_frame_count"], "openpilot.camera_dropped_frame_count")
    _counter(data["model_skipped_frame_count"], "openpilot.model_skipped_frame_count")
    return data


def _validate_tesla(raw: Any) -> dict[str, Any]:
    data = _object(raw, "tesla")
    _exact_keys(
        data,
        {
            "hardware_generation",
            "vehicle_platform",
            "firmware_version",
            "fsd_version",
            "capture_id",
            "bus",
            "physical_tap",
            "decoder_version",
            "clock_domain",
            "timing_provenance",
            "capture_quality",
            "filter_mode",
            "rx_dropped_count",
            "rx_overflow_count",
            "write_path_present",
        },
        "tesla",
    )
    for field in (
        "hardware_generation",
        "vehicle_platform",
        "firmware_version",
        "fsd_version",
        "capture_id",
        "bus",
        "physical_tap",
        "decoder_version",
        "clock_domain",
        "timing_provenance",
        "filter_mode",
    ):
        _string(data[field], f"tesla.{field}")
    _enum(data["capture_quality"], CAPTURE_QUALITIES, "tesla.capture_quality")
    _counter(data["rx_dropped_count"], "tesla.rx_dropped_count")
    _counter(data["rx_overflow_count"], "tesla.rx_overflow_count")
    if not isinstance(data["write_path_present"], bool):
        raise TeslaBenchmarkError("tesla.write_path_present must be boolean")
    if data["write_path_present"]:
        raise TeslaBenchmarkError("a Tesla write path is prohibited in benchmark episodes")
    return data


def _validate_alignment(raw: Any, comparison_mode: str, openpilot: dict[str, Any], tesla: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    data = _object(raw, "alignment")
    _exact_keys(data, {"method", "max_error_ms"}, "alignment")
    method = _enum(data["method"], ALIGNMENT_METHODS, "alignment.method")

    if comparison_mode == "MATCHED_SCENARIO":
        if method != "MATCHED_SCENARIO_ONLY":
            raise TeslaBenchmarkError("MATCHED_SCENARIO requires MATCHED_SCENARIO_ONLY alignment")
        if data["max_error_ms"] is not None:
            raise TeslaBenchmarkError("matched scenarios cannot claim a temporal alignment error")
        return data, False

    if method == "MATCHED_SCENARIO_ONLY":
        raise TeslaBenchmarkError(f"{comparison_mode} requires real timestamp or replay alignment")
    max_error_ms = _finite_number(data["max_error_ms"], "alignment.max_error_ms")
    if max_error_ms < 0:
        raise TeslaBenchmarkError("alignment.max_error_ms cannot be negative")
    if method == "SHARED_MONOTONIC_CLOCK" and openpilot["clock_domain"] != tesla["clock_domain"]:
        raise TeslaBenchmarkError("SHARED_MONOTONIC_CLOCK requires equal clock_domain values")
    trusted_sources = (
        openpilot["timing_provenance"] in TRUSTED_TIMING
        and tesla["timing_provenance"] in TRUSTED_TIMING
    )
    return data, trusted_sources and max_error_ms <= 50.0


def _validate_signals(raw: Any) -> tuple[int, int]:
    if not isinstance(raw, list) or not raw:
        raise TeslaBenchmarkError("signals must be a non-empty list")
    comparable = 0
    cross_validated = 0
    seen: set[str] = set()
    for index, raw_signal in enumerate(raw):
        location = f"signals[{index}]"
        signal = _object(raw_signal, location)
        _exact_keys(signal, {"name", "status", "value", "unit", "evidence"}, location)
        name = _enum(signal["name"], SIGNAL_NAMES, f"{location}.name")
        if name in seen:
            raise TeslaBenchmarkError(f"duplicate benchmark signal: {name}")
        seen.add(name)
        status = _enum(signal["status"], SIGNAL_STATUSES, f"{location}.status")
        _string(signal["unit"], f"{location}.unit")
        evidence = signal["evidence"]
        if (
            not isinstance(evidence, list)
            or not all(isinstance(item, str) for item in evidence)
            or len(evidence) != len(set(evidence))
        ):
            raise TeslaBenchmarkError(f"{location}.evidence must be a duplicate-free list")
        for evidence_type in evidence:
            _enum(evidence_type, EVIDENCE_TYPES, f"{location}.evidence")

        if status == "UNKNOWN":
            if signal["value"] is not None:
                raise TeslaBenchmarkError(f"{location}: UNKNOWN must preserve value as null")
            if evidence:
                raise TeslaBenchmarkError(f"{location}: UNKNOWN cannot claim evidence")
            continue
        if signal["value"] is None:
            raise TeslaBenchmarkError(f"{location}: {status} requires an observed value")
        if not evidence:
            raise TeslaBenchmarkError(f"{location}: {status} requires evidence")
        comparable += 1
        if status == "CROSS_SOURCE_VALIDATED":
            if len(evidence) < 2:
                raise TeslaBenchmarkError(f"{location}: CROSS_SOURCE_VALIDATED requires two evidence types")
            cross_validated += 1
    return comparable, cross_validated


def evaluate_tesla_benchmark(manifest: dict[str, Any], *, expected_openpilot_commit: str) -> TeslaBenchmarkReport:
    episode_id = str(manifest.get("episode_id", "UNKNOWN")) if isinstance(manifest, dict) else "UNKNOWN"
    comparison_mode = str(manifest.get("comparison_mode", "UNKNOWN")) if isinstance(manifest, dict) else "UNKNOWN"
    try:
        data = _object(manifest, "benchmark manifest")
        _exact_keys(
            data,
            {
                "schema_version",
                "episode_id",
                "comparison_mode",
                "actuation_authority",
                "openpilot",
                "tesla",
                "alignment",
                "signals",
            },
            "benchmark manifest",
        )
        if data["schema_version"] != 1:
            raise TeslaBenchmarkError("benchmark manifest schema_version must be 1")
        episode_id = _string(data["episode_id"], "episode_id")
        comparison_mode = _enum(data["comparison_mode"], COMPARISON_MODES, "comparison_mode")
        if data["actuation_authority"] != "NONE":
            raise TeslaBenchmarkError("actuation_authority must be NONE")
        openpilot = _validate_openpilot(data["openpilot"], expected_openpilot_commit)
        tesla = _validate_tesla(data["tesla"])
        _, aligned = _validate_alignment(data["alignment"], comparison_mode, openpilot, tesla)
        comparable, cross_validated = _validate_signals(data["signals"])
    except TeslaBenchmarkError as exc:
        return TeslaBenchmarkReport(
            schema_version=1,
            episode_id=episode_id,
            comparison_mode=comparison_mode,
            classification="REJECTED",
            comparable_signal_count=0,
            cross_validated_signal_count=0,
            reasons=(),
            errors=(str(exc),),
        )

    reasons: list[str] = []
    full_rate = True
    for source_name, source in (("openpilot", openpilot), ("tesla", tesla)):
        if source["capture_quality"] != "FULL_RATE_CANDIDATE":
            full_rate = False
            reasons.append(f"{source_name.upper()}_CAPTURE_NOT_FULL_RATE")
    drops = tesla["rx_dropped_count"]
    overflows = tesla["rx_overflow_count"]
    if drops is None or overflows is None:
        full_rate = False
        reasons.append("TESLA_LOSS_COUNTERS_UNKNOWN")
    elif drops > 0 or overflows > 0:
        full_rate = False
        reasons.append("TESLA_CAPTURE_LOSS_OBSERVED")

    openpilot_drops = openpilot["camera_dropped_frame_count"]
    openpilot_skips = openpilot["model_skipped_frame_count"]
    if openpilot_drops is None or openpilot_skips is None:
        full_rate = False
        reasons.append("OPENPILOT_LOSS_COUNTERS_UNKNOWN")
    elif openpilot_drops > 0 or openpilot_skips > 0:
        full_rate = False
        reasons.append("OPENPILOT_FRAME_LOSS_OBSERVED")

    if comparison_mode == "MATCHED_SCENARIO":
        classification = "SCENARIO_BENCHMARK_ONLY"
        reasons.append("NOT_THE_SAME_PHYSICAL_EPISODE")
    elif comparable == 0:
        classification = "OBSERVATION_ONLY"
        reasons.append("NO_COMPARABLE_SIGNALS")
    elif not aligned:
        classification = "OBSERVATION_ONLY"
        reasons.append("TIMING_NOT_QUALIFIED")
    elif not full_rate:
        classification = "OBSERVATION_ONLY"
    elif cross_validated == 0:
        classification = "OBSERVATION_ONLY"
        reasons.append("NO_CROSS_SOURCE_VALIDATED_TESLA_SIGNAL")
    else:
        classification = "BEHAVIOURAL_COMPARISON_READY"

    return TeslaBenchmarkReport(
        schema_version=1,
        episode_id=episode_id,
        comparison_mode=comparison_mode,
        classification=classification,
        comparable_signal_count=comparable,
        cross_validated_signal_count=cross_validated,
        reasons=tuple(dict.fromkeys(reasons)),
        errors=(),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--expected-openpilot-commit", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    report = evaluate_tesla_benchmark(
        manifest,
        expected_openpilot_commit=args.expected_openpilot_commit,
    ).to_dict()
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        args.output.write_text(rendered, encoding="utf-8")
    return 0 if report["classification"] != "REJECTED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
