"""Compare passive FlexRay captures against a known-good reference trace.

This module is offline-only. It contains no bus transmit path and grants no
vehicle-control authority. Its purpose is to quantify whether a candidate
capture interface reproduces the same observed FlexRay traffic as a reference
interface.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import median
from typing import Any, Iterable

from validation.flexray_capture_validator import validate_records


FrameKey = tuple[str | None, int | None, int, int]


@dataclass
class TraceComparison:
    reference_count: int
    candidate_count: int
    matched_count: int = 0
    missing_keys: list[FrameKey] = field(default_factory=list)
    extra_keys: list[FrameKey] = field(default_factory=list)
    payload_mismatches: list[FrameKey] = field(default_factory=list)
    length_mismatches: list[FrameKey] = field(default_factory=list)
    reference_errors: list[str] = field(default_factory=list)
    candidate_errors: list[str] = field(default_factory=list)
    clock_offset_ns: int | None = None
    max_abs_residual_ns: int | None = None
    median_abs_residual_ns: int | None = None

    @property
    def exact_frame_fidelity(self) -> bool:
        return (
            not self.reference_errors
            and not self.candidate_errors
            and not self.missing_keys
            and not self.extra_keys
            and not self.payload_mismatches
            and not self.length_mismatches
            and self.reference_count == self.candidate_count == self.matched_count
        )

    def classify(
        self,
        *,
        replay_residual_limit_ns: int = 10_000_000,
        state_source_residual_limit_ns: int = 2_000_000,
    ) -> str:
        """Return a conservative passive-capture qualification.

        Thresholds are engineering defaults, not vehicle-control limits. They
        are intentionally configurable and should be tightened or replaced by
        measured requirements before a real interface is promoted.
        """
        if self.reference_errors or self.candidate_errors:
            return "REJECTED"
        if not self.exact_frame_fidelity:
            return "OBSERVATION_ONLY"
        if self.max_abs_residual_ns is None:
            return "OBSERVATION_ONLY"
        if self.max_abs_residual_ns <= state_source_residual_limit_ns:
            return "STATE_SOURCE_CANDIDATE"
        if self.max_abs_residual_ns <= replay_residual_limit_ns:
            return "REPLAY_TRUSTED"
        return "OBSERVATION_ONLY"


def _index(records: list[dict[str, Any]]) -> dict[FrameKey, dict[str, Any]]:
    """Index frames using channel/cycle/slot plus occurrence ordinal.

    The occurrence ordinal avoids silently collapsing repeated frames when a
    trace contains duplicate (channel, cycle, slot) tuples, including cycle
    counter wrap-around.
    """
    counts: dict[tuple[str | None, int | None, int], int] = {}
    indexed: dict[FrameKey, dict[str, Any]] = {}

    for record in records:
        base = (record.get("channel"), record.get("cycle"), record["slot_id"])
        ordinal = counts.get(base, 0)
        counts[base] = ordinal + 1
        indexed[(base[0], base[1], base[2], ordinal)] = record

    return indexed


def compare_traces(
    reference_records: Iterable[dict[str, Any]],
    candidate_records: Iterable[dict[str, Any]],
) -> TraceComparison:
    """Compare a candidate receive-only trace with a reference trace.

    A constant clock offset between independent capture computers is removed
    using the median matched timestamp delta. Remaining residuals therefore
    describe relative timing/jitter rather than wall-clock alignment.
    """
    reference = list(reference_records)
    candidate = list(candidate_records)
    reference_validation = validate_records(reference)
    candidate_validation = validate_records(candidate)

    result = TraceComparison(
        reference_count=len(reference),
        candidate_count=len(candidate),
        reference_errors=list(reference_validation.errors),
        candidate_errors=list(candidate_validation.errors),
    )

    if result.reference_errors or result.candidate_errors:
        return result

    ref_index = _index(reference)
    cand_index = _index(candidate)
    ref_keys = set(ref_index)
    cand_keys = set(cand_index)

    result.missing_keys = sorted(ref_keys - cand_keys, key=str)
    result.extra_keys = sorted(cand_keys - ref_keys, key=str)

    time_deltas: list[int] = []

    for key in sorted(ref_keys & cand_keys, key=str):
        ref = ref_index[key]
        cand = cand_index[key]
        result.matched_count += 1

        if ref["payload_length"] != cand["payload_length"]:
            result.length_mismatches.append(key)
        if ref["payload_hex"].lower() != cand["payload_hex"].lower():
            result.payload_mismatches.append(key)

        time_deltas.append(cand["host_time_ns"] - ref["host_time_ns"])

    if time_deltas:
        offset = int(median(time_deltas))
        residuals = [delta - offset for delta in time_deltas]
        abs_residuals = [abs(value) for value in residuals]
        result.clock_offset_ns = offset
        result.max_abs_residual_ns = max(abs_residuals)
        result.median_abs_residual_ns = int(median(abs_residuals))

    return result
