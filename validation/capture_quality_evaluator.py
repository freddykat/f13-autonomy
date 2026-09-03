"""Audit capture quality from recorder provenance and observable statistics.

This module is offline-only. It evaluates already-recorded CAN or FlexRay data
and contains no bus, diagnostic, or vehicle-control interface.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

from validation.flexray_capture_validator import validate_records


CAPTURE_QUALITIES = {"UNKNOWN", "LOSSY", "OBSERVATION_ONLY", "FULL_RATE_CANDIDATE"}
FILTER_MODES = {"UNKNOWN", "ACCEPT_ALL", "SINGLE_ID_HARDWARE", "MULTI_ID_HARDWARE", "SOFTWARE"}
SEQUENCE_PROVENANCE = {"UNKNOWN", "ROW_ORDINAL", "ADAPTER_MONOTONIC"}
CYCLE_PROVENANCE = {"UNKNOWN", "BUS_CYCLE", "SCHEDULE_VALIDATED"}
REFERENCE_FRAME_FIDELITY = {"NOT_COMPARED", "EXACT", "MISMATCH", "INVALID"}
TRUSTED_PER_FRAME_TIMING = {"per_frame_monotonic", "hardware_timestamp", "reference_export"}

SUPPLEMENTAL_FIELDS = {
    "sequence_provenance",
    "sequence_gap_count",
    "sequence_duplicate_count",
    "sequence_regression_count",
    "cycle_provenance",
    "cycle_anomaly_count",
    "expected_rate_checked",
    "reference_frame_fidelity",
}


class CaptureQualityError(ValueError):
    pass


@dataclass
class CaptureQualityReport:
    capture_id: str
    transport: str
    record_count: int
    declared_quality: str
    evaluated_quality: str
    timing_quality: str
    positive_evidence: list[str] = field(default_factory=list)
    negative_evidence: list[str] = field(default_factory=list)
    unknown_evidence: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    actuation_authority: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _nonnegative(value: Any, name: str, *, nullable: bool = True) -> int | None:
    if value is None and nullable:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        suffix = " or null" if nullable else ""
        raise CaptureQualityError(f"{name} must be a non-negative integer{suffix}")
    return value


def _optional_bool(value: Any, name: str) -> bool | None:
    if value not in (True, False, None):
        raise CaptureQualityError(f"{name} must be true, false or null")
    return value


def _normalize_supplemental(raw: dict[str, Any] | None) -> dict[str, Any]:
    supplied = {} if raw is None else raw
    if not isinstance(supplied, dict):
        raise CaptureQualityError("supplemental evidence must be an object")
    unknown = sorted(set(supplied) - SUPPLEMENTAL_FIELDS)
    if unknown:
        raise CaptureQualityError(f"unknown supplemental evidence fields: {', '.join(unknown)}")

    normalized = {
        "sequence_provenance": supplied.get("sequence_provenance", "UNKNOWN"),
        "sequence_gap_count": supplied.get("sequence_gap_count"),
        "sequence_duplicate_count": supplied.get("sequence_duplicate_count"),
        "sequence_regression_count": supplied.get("sequence_regression_count"),
        "cycle_provenance": supplied.get("cycle_provenance", "UNKNOWN"),
        "cycle_anomaly_count": supplied.get("cycle_anomaly_count"),
        "expected_rate_checked": supplied.get("expected_rate_checked"),
        "reference_frame_fidelity": supplied.get("reference_frame_fidelity", "NOT_COMPARED"),
    }

    if normalized["sequence_provenance"] not in SEQUENCE_PROVENANCE:
        raise CaptureQualityError("unsupported sequence_provenance")
    if normalized["cycle_provenance"] not in CYCLE_PROVENANCE:
        raise CaptureQualityError("unsupported cycle_provenance")
    if normalized["reference_frame_fidelity"] not in REFERENCE_FRAME_FIDELITY:
        raise CaptureQualityError("unsupported reference_frame_fidelity")
    _optional_bool(normalized["expected_rate_checked"], "expected_rate_checked")
    for name in (
        "sequence_gap_count",
        "sequence_duplicate_count",
        "sequence_regression_count",
        "cycle_anomaly_count",
    ):
        normalized[name] = _nonnegative(normalized[name], name)
    return normalized


def _timing_quality(record_count: int, provenances: set[Any], regressions: int) -> str:
    if regressions:
        return "INVALID"
    if record_count == 0:
        return "UNKNOWN"
    if provenances and provenances <= TRUSTED_PER_FRAME_TIMING:
        return "PER_FRAME_CANDIDATE"
    return "TIMING_UNVERIFIED"


def _evaluate(
    *,
    capture_id: str,
    transport: str,
    record_count: int,
    declared_quality: str,
    listen_only: bool | None,
    filter_mode: str,
    rx_queue_depth: int | None,
    rx_dropped_count: int | None,
    rx_overflow_count: int | None,
    structural_error_count: int,
    timestamp_regression_count: int,
    timing_provenances: set[Any],
    supplemental: dict[str, Any],
) -> CaptureQualityReport:
    if not isinstance(capture_id, str) or not capture_id:
        raise CaptureQualityError("capture_id must be a non-empty string")
    if transport not in {"CAN", "FLEXRAY"}:
        raise CaptureQualityError("transport must be CAN or FLEXRAY")
    if declared_quality not in CAPTURE_QUALITIES:
        raise CaptureQualityError("unsupported declared capture quality")
    if filter_mode not in FILTER_MODES:
        raise CaptureQualityError("unsupported filter_mode")
    _optional_bool(listen_only, "listen_only")
    record_count = _nonnegative(record_count, "record_count", nullable=False)
    structural_error_count = _nonnegative(
        structural_error_count, "structural_error_count", nullable=False
    )
    timestamp_regression_count = _nonnegative(
        timestamp_regression_count, "timestamp_regression_count", nullable=False
    )
    rx_queue_depth = _nonnegative(rx_queue_depth, "rx_queue_depth")
    rx_dropped_count = _nonnegative(rx_dropped_count, "rx_dropped_count")
    rx_overflow_count = _nonnegative(rx_overflow_count, "rx_overflow_count")

    positive: list[str] = []
    negative: list[str] = []
    unknowns: list[str] = []

    if declared_quality == "LOSSY":
        negative.append("source explicitly declares the capture lossy")
    if structural_error_count:
        negative.append(f"{structural_error_count} structurally invalid records")
    if timestamp_regression_count:
        negative.append(f"{timestamp_regression_count} timestamp regressions")
    if rx_dropped_count is not None and rx_dropped_count > 0:
        negative.append(f"adapter reports {rx_dropped_count} dropped frames")
    if rx_overflow_count is not None and rx_overflow_count > 0:
        negative.append(f"adapter reports {rx_overflow_count} receive overflows")

    sequence_counts = [
        supplemental["sequence_gap_count"],
        supplemental["sequence_duplicate_count"],
        supplemental["sequence_regression_count"],
    ]
    if any(value is not None and value > 0 for value in sequence_counts):
        negative.append("capture sequence contains gaps, duplicates or regressions")
    if (
        supplemental["cycle_anomaly_count"] is not None
        and supplemental["cycle_anomaly_count"] > 0
    ):
        negative.append("validated bus-cycle statistics contain anomalies")

    reference = supplemental["reference_frame_fidelity"]
    if reference in {"MISMATCH", "INVALID"}:
        negative.append(f"reference frame comparison is {reference.lower()}")
    if supplemental["expected_rate_checked"] is False:
        negative.append("observed frame rate failed its explicit expectation")

    counters_known_zero = rx_dropped_count == 0 and rx_overflow_count == 0
    if counters_known_zero:
        positive.append("adapter drop and overflow counters are known zero")
    else:
        if rx_dropped_count is None:
            unknowns.append("rx_dropped_count is unavailable")
        if rx_overflow_count is None:
            unknowns.append("rx_overflow_count is unavailable")

    if rx_queue_depth is None:
        unknowns.append("rx_queue_depth is unavailable")
    elif rx_queue_depth > 0:
        positive.append("receive queue depth is recorded")

    sequence_clean = (
        supplemental["sequence_provenance"] == "ADAPTER_MONOTONIC"
        and all(value == 0 for value in sequence_counts)
    )
    if sequence_clean:
        positive.append("adapter sequence is continuous")
    elif supplemental["sequence_provenance"] in {"UNKNOWN", "ROW_ORDINAL"}:
        unknowns.append("no trustworthy adapter-side sequence continuity evidence")

    cycle_clean = (
        supplemental["cycle_provenance"] == "SCHEDULE_VALIDATED"
        and supplemental["cycle_anomaly_count"] == 0
    )
    if cycle_clean:
        positive.append("bus-cycle schedule validation found no anomalies")
    elif supplemental["cycle_provenance"] != "SCHEDULE_VALIDATED":
        unknowns.append("bus-cycle schedule has not been validated")

    if reference == "EXACT":
        positive.append("simultaneous reference comparison has exact frame fidelity")
    elif reference == "NOT_COMPARED":
        unknowns.append("no simultaneous reference comparison")

    if supplemental["expected_rate_checked"] is True:
        positive.append("expected message/frame rate was independently checked")
    elif supplemental["expected_rate_checked"] is None:
        unknowns.append("expected message/frame rate was not checked")

    if filter_mode in {"SINGLE_ID_HARDWARE", "MULTI_ID_HARDWARE"}:
        positive.append("hardware acceptance filtering is declared")
    elif filter_mode == "UNKNOWN":
        unknowns.append("filter mode is unknown")

    if listen_only is True:
        positive.append("listen-only mode is explicitly declared")
    elif listen_only is None:
        unknowns.append("listen-only mode is unknown")

    strong_reference = reference == "EXACT"
    rate_confirmed = supplemental["expected_rate_checked"] is True
    continuity_confirmed = sequence_clean or cycle_clean
    filtered_zero_loss = (
        counters_known_zero
        and filter_mode in {"SINGLE_ID_HARDWARE", "MULTI_ID_HARDWARE"}
    )

    if negative:
        evaluated = "LOSSY"
    elif record_count == 0:
        evaluated = "OBSERVATION_ONLY"
        unknowns.append("capture contains no records")
    elif listen_only is not True:
        evaluated = "OBSERVATION_ONLY"
        if listen_only is False:
            unknowns.append("capture was not declared listen-only")
    elif declared_quality == "OBSERVATION_ONLY" and not strong_reference:
        evaluated = "OBSERVATION_ONLY"
        unknowns.append("source declaration caps capture at observation-only")
    elif strong_reference or rate_confirmed or continuity_confirmed or filtered_zero_loss:
        evaluated = "FULL_RATE_CANDIDATE"
    else:
        evaluated = "OBSERVATION_ONLY"

    return CaptureQualityReport(
        capture_id=capture_id,
        transport=transport,
        record_count=record_count,
        declared_quality=declared_quality,
        evaluated_quality=evaluated,
        timing_quality=_timing_quality(
            record_count, timing_provenances, timestamp_regression_count
        ),
        positive_evidence=positive,
        negative_evidence=negative,
        unknown_evidence=unknowns,
        metrics={
            "filter_mode": filter_mode,
            "listen_only": listen_only,
            "rx_queue_depth": rx_queue_depth,
            "rx_dropped_count": rx_dropped_count,
            "rx_overflow_count": rx_overflow_count,
            "structural_error_count": structural_error_count,
            "timestamp_regression_count": timestamp_regression_count,
            **supplemental,
        },
    )


def _scan_can_frames(frames: Any, declared_count: Any) -> tuple[int, int, int, set[Any]]:
    if not isinstance(frames, list):
        raise CaptureQualityError("CAN capture frames must be an array")

    structural_errors = 0
    timestamp_regressions = 0
    timing_provenances: set[Any] = set()
    previous_time: int | None = None

    if isinstance(declared_count, bool) or not isinstance(declared_count, int):
        structural_errors += 1
    elif declared_count != len(frames):
        structural_errors += 1

    for frame in frames:
        if not isinstance(frame, dict):
            structural_errors += 1
            continue

        timestamp = frame.get("timestamp_ns")
        if isinstance(timestamp, bool) or not isinstance(timestamp, int) or timestamp < 0:
            structural_errors += 1
        else:
            if previous_time is not None and timestamp < previous_time:
                timestamp_regressions += 1
            previous_time = timestamp

        provenance = frame.get("timestamp_provenance")
        if provenance is not None and not isinstance(provenance, str):
            structural_errors += 1
            timing_provenances.add("<invalid>")
        else:
            timing_provenances.add(provenance)

        data_hex = frame.get("data_hex")
        dlc = frame.get("dlc")
        if not isinstance(data_hex, str) or len(data_hex) % 2:
            structural_errors += 1
            continue
        try:
            payload = bytes.fromhex(data_hex)
        except ValueError:
            structural_errors += 1
            continue
        if isinstance(dlc, bool) or not isinstance(dlc, int) or dlc != len(payload):
            structural_errors += 1

    return len(frames), structural_errors, timestamp_regressions, timing_provenances


def evaluate_can_capture(
    capture: dict[str, Any],
    *,
    supplemental_evidence: dict[str, Any] | None = None,
) -> CaptureQualityReport:
    if not isinstance(capture, dict):
        raise CaptureQualityError("CAN capture must be an object")
    if capture.get("schema_version") != 2:
        raise CaptureQualityError("CAN capture schema_version must equal 2")
    if capture.get("mode") != "read_only_can_capture_import":
        raise CaptureQualityError("unsupported CAN capture mode")

    record_count, structural_errors, timestamp_regressions, provenances = _scan_can_frames(
        capture.get("frames"), capture.get("frame_count")
    )
    supplemental = _normalize_supplemental(supplemental_evidence)
    return _evaluate(
        capture_id=capture.get("capture_id"),
        transport="CAN",
        record_count=record_count,
        declared_quality=capture.get("capture_quality"),
        listen_only=capture.get("listen_only"),
        filter_mode=capture.get("filter_mode"),
        rx_queue_depth=capture.get("rx_queue_depth"),
        rx_dropped_count=capture.get("rx_dropped_count"),
        rx_overflow_count=capture.get("rx_overflow_count"),
        structural_error_count=structural_errors,
        timestamp_regression_count=timestamp_regressions,
        timing_provenances=provenances,
        supplemental=supplemental,
    )


def _sequence_statistics(records: list[dict[str, Any]]) -> tuple[int, int]:
    duplicates = 0
    regressions = 0
    previous: int | None = None
    for record in records:
        sequence = record.get("capture_sequence") if isinstance(record, dict) else None
        if not isinstance(sequence, int) or isinstance(sequence, bool):
            continue
        if previous is not None:
            if sequence == previous:
                duplicates += 1
            elif sequence < previous:
                regressions += 1
        previous = sequence
    return duplicates, regressions


def evaluate_flexray_capture(
    records: Iterable[dict[str, Any]],
    *,
    provenance: dict[str, Any],
    supplemental_evidence: dict[str, Any] | None = None,
) -> CaptureQualityReport:
    records = list(records)
    if not isinstance(provenance, dict):
        raise CaptureQualityError("FlexRay provenance must be an object")

    validation = validate_records(records)
    timestamp_regressions = sum("host_time_ns regressed" in error for error in validation.errors)
    duplicates, regressions = _sequence_statistics(records)
    structural_errors = sum(
        "host_time_ns regressed" not in error
        and "capture_sequence did not increase" not in error
        for error in validation.errors
    )

    supplemental = _normalize_supplemental(supplemental_evidence)
    if supplemental["sequence_gap_count"] is None:
        supplemental["sequence_gap_count"] = len(validation.sequence_gaps)
    if supplemental["sequence_duplicate_count"] is None:
        supplemental["sequence_duplicate_count"] = duplicates
    if supplemental["sequence_regression_count"] is None:
        supplemental["sequence_regression_count"] = regressions

    timing_provenances: set[Any] = set()
    for record in records:
        if not isinstance(record, dict):
            continue
        provenance_value = record.get("timing_provenance")
        if provenance_value is None or isinstance(provenance_value, str):
            timing_provenances.add(provenance_value)
        else:
            structural_errors += 1
            timing_provenances.add("<invalid>")
    return _evaluate(
        capture_id=provenance.get("capture_id"),
        transport="FLEXRAY",
        record_count=len(records),
        declared_quality=provenance.get("capture_quality", "UNKNOWN"),
        listen_only=provenance.get("listen_only"),
        filter_mode=provenance.get("filter_mode", "UNKNOWN"),
        rx_queue_depth=provenance.get("rx_queue_depth"),
        rx_dropped_count=provenance.get("rx_dropped_count"),
        rx_overflow_count=provenance.get("rx_overflow_count"),
        structural_error_count=structural_errors,
        timestamp_regression_count=timestamp_regressions,
        timing_provenances=timing_provenances,
        supplemental=supplemental,
    )


def evaluate_document(
    document: dict[str, Any],
    *,
    supplemental_evidence: dict[str, Any] | None = None,
) -> CaptureQualityReport:
    if document.get("mode") == "read_only_can_capture_import":
        return evaluate_can_capture(document, supplemental_evidence=supplemental_evidence)
    if document.get("transport") == "FLEXRAY" and isinstance(document.get("records"), list):
        return evaluate_flexray_capture(
            document["records"],
            provenance=document.get("provenance", {}),
            supplemental_evidence=supplemental_evidence,
        )
    raise CaptureQualityError("cannot determine capture document transport")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate recorder quality for an offline CAN or FlexRay capture"
    )
    parser.add_argument("capture", type=Path)
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    document = json.loads(args.capture.read_text(encoding="utf-8"))
    supplemental = (
        None
        if args.evidence is None
        else json.loads(args.evidence.read_text(encoding="utf-8"))
    )
    report = evaluate_document(document, supplemental_evidence=supplemental).to_dict()
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
