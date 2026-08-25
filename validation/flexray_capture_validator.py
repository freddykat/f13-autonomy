"""Receive-only FlexRay trace validation helpers.

This module validates canonical offline capture records only. It contains no bus
transmit path and no vehicle-control interface.
"""

from dataclasses import dataclass, field
from typing import Any, Iterable


@dataclass
class ValidationReport:
    record_count: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    sequence_gaps: list[tuple[int, int]] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.errors


def _require_int(record: dict[str, Any], key: str, index: int, report: ValidationReport) -> int | None:
    value = record.get(key)
    if not isinstance(value, int):
        report.errors.append(f"record[{index}] {key} must be int")
        return None
    return value


def validate_records(records: Iterable[dict[str, Any]]) -> ValidationReport:
    """Validate canonical receive-only FlexRay capture records.

    Checks structural validity, monotonic timestamps/sequence, payload length,
    and records observable sequence gaps. A sequence gap is reported but is not
    automatically classified as an error because it may represent an explicitly
    observable adapter drop. Downstream conformance code can compare the gap
    against adapter error/drop counters.
    """

    report = ValidationReport()
    prev_time: int | None = None
    prev_seq: int | None = None

    for index, record in enumerate(records):
        report.record_count += 1
        if not isinstance(record, dict):
            report.errors.append(f"record[{index}] must be object")
            continue

        host_time = _require_int(record, "host_time_ns", index, report)
        sequence = _require_int(record, "capture_sequence", index, report)
        slot_id = _require_int(record, "slot_id", index, report)
        payload_length = _require_int(record, "payload_length", index, report)

        if host_time is not None:
            if host_time < 0:
                report.errors.append(f"record[{index}] host_time_ns must be >= 0")
            if prev_time is not None and host_time < prev_time:
                report.errors.append(f"record[{index}] host_time_ns regressed")
            prev_time = host_time

        if sequence is not None:
            if sequence < 0:
                report.errors.append(f"record[{index}] capture_sequence must be >= 0")
            if prev_seq is not None:
                if sequence <= prev_seq:
                    report.errors.append(f"record[{index}] capture_sequence did not increase")
                elif sequence != prev_seq + 1:
                    report.sequence_gaps.append((prev_seq, sequence))
                    report.warnings.append(
                        f"capture sequence gap: {prev_seq} -> {sequence}; correlate with adapter drop/error counters"
                    )
            prev_seq = sequence

        if slot_id is not None and slot_id < 0:
            report.errors.append(f"record[{index}] slot_id must be >= 0")

        cycle = record.get("cycle")
        if cycle is not None and (not isinstance(cycle, int) or cycle < 0):
            report.errors.append(f"record[{index}] cycle must be non-negative int or null")

        payload_hex = record.get("payload_hex")
        if not isinstance(payload_hex, str):
            report.errors.append(f"record[{index}] payload_hex must be string")
        else:
            try:
                payload = bytes.fromhex(payload_hex)
            except ValueError:
                report.errors.append(f"record[{index}] payload_hex is not valid hex")
            else:
                if payload_length is not None and len(payload) != payload_length:
                    report.errors.append(
                        f"record[{index}] payload length mismatch: decoded={len(payload)} declared={payload_length}"
                    )

        channel = record.get("channel")
        if channel is not None and not isinstance(channel, str):
            report.errors.append(f"record[{index}] channel must be string or null")

        source = record.get("source")
        if not isinstance(source, str) or not source:
            report.errors.append(f"record[{index}] source must be non-empty string")

    return report
