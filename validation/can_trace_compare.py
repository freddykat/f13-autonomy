"""Compare simultaneous canonical CAN captures without decoding vehicle signals.

The comparator is offline-only. It aligns receive frames per logical channel and
CAN frame selector, compares payloads byte-for-byte, and keeps timing fidelity
separate from frame fidelity. It contains no CAN transmit or vehicle interface.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field, fields
from difflib import SequenceMatcher
from pathlib import Path
from statistics import median
from typing import Any


FRAME_FIDELITIES = {
    "EXACT",
    "MISMATCH",
    "INVALID",
    "NOT_SIMULTANEOUS",
    "UNQUALIFIED_REFERENCE",
}
TRUSTED_TIMING = {"per_frame_monotonic", "hardware_timestamp", "reference_export"}


class CanTraceComparisonError(ValueError):
    pass


@dataclass(frozen=True)
class CanTraceComparisonReport:
    candidate_capture_id: str
    reference_capture_id: str
    simultaneous: bool
    reference_capture_quality: str
    frame_fidelity: str
    timing_fidelity: str
    reference_rx_count: int
    candidate_rx_count: int
    matched_frame_count: int
    payload_mismatch_count: int
    missing_frame_count: int
    extra_frame_count: int
    ignored_reference_tx_count: int
    ignored_candidate_tx_count: int
    clock_offset_ns: int | None
    median_absolute_timing_residual_ns: int | None
    max_absolute_timing_residual_ns: int | None
    mismatch_examples: list[dict[str, Any]] = field(default_factory=list)
    schema_version: int = 1
    mode: str = "offline_simultaneous_can_compare"
    actuation_authority: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "CanTraceComparisonReport":
        if not isinstance(raw, dict):
            raise CanTraceComparisonError("comparison report must be an object")
        expected = {item.name for item in fields(cls)}
        missing = sorted(expected - set(raw))
        unknown = sorted(set(raw) - expected)
        if missing:
            raise CanTraceComparisonError(f"comparison report missing fields: {', '.join(missing)}")
        if unknown:
            raise CanTraceComparisonError(f"comparison report contains unknown fields: {', '.join(unknown)}")
        report = cls(**raw)
        report.validate()
        return report

    def validate(self) -> None:
        if self.schema_version != 1 or self.mode != "offline_simultaneous_can_compare":
            raise CanTraceComparisonError("unsupported CAN comparison report schema or mode")
        if self.actuation_authority != "NONE":
            raise CanTraceComparisonError("CAN comparison cannot grant actuation authority")
        if not isinstance(self.candidate_capture_id, str) or not self.candidate_capture_id:
            raise CanTraceComparisonError("candidate_capture_id must be a non-empty string")
        if not isinstance(self.reference_capture_id, str) or not self.reference_capture_id:
            raise CanTraceComparisonError("reference_capture_id must be a non-empty string")
        if not isinstance(self.simultaneous, bool):
            raise CanTraceComparisonError("simultaneous must be boolean")
        if self.frame_fidelity not in FRAME_FIDELITIES:
            raise CanTraceComparisonError("unsupported frame_fidelity")
        if self.reference_capture_quality not in {
            "UNKNOWN", "LOSSY", "OBSERVATION_ONLY", "FULL_RATE_CANDIDATE"
        }:
            raise CanTraceComparisonError("unsupported reference_capture_quality")
        for name in (
            "reference_rx_count", "candidate_rx_count", "matched_frame_count",
            "payload_mismatch_count", "missing_frame_count", "extra_frame_count",
            "ignored_reference_tx_count", "ignored_candidate_tx_count",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise CanTraceComparisonError(f"{name} must be a non-negative integer")
        if not isinstance(self.mismatch_examples, list):
            raise CanTraceComparisonError("mismatch_examples must be an array")
        if self.frame_fidelity == "EXACT" and not self.qualifies_candidate(self.candidate_capture_id):
            raise CanTraceComparisonError("EXACT report invariants are inconsistent")

    def qualifies_candidate(self, capture_id: str) -> bool:
        return (
            self.candidate_capture_id == capture_id
            and self.simultaneous
            and self.reference_capture_quality == "FULL_RATE_CANDIDATE"
            and self.frame_fidelity == "EXACT"
            and self.reference_rx_count > 0
            and self.reference_rx_count == self.candidate_rx_count == self.matched_frame_count
            and self.payload_mismatch_count == 0
            and self.missing_frame_count == 0
            and self.extra_frame_count == 0
        )


def _validate_channel_map(raw: dict[str, str] | None, name: str) -> dict[str, str]:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise CanTraceComparisonError(f"{name} must be an object")
    result: dict[str, str] = {}
    for source, logical in raw.items():
        if not isinstance(source, str) or not source or not isinstance(logical, str) or not logical:
            raise CanTraceComparisonError(f"{name} keys and values must be non-empty strings")
        result[source] = logical
    if len(set(result.values())) != len(result):
        raise CanTraceComparisonError(f"{name} cannot map multiple source channels to one logical channel")
    return result


def _logical_channel(channel: Any, mapping: dict[str, str], side: str) -> str:
    if not isinstance(channel, str) or not channel:
        raise CanTraceComparisonError(f"{side} frame channel must be a non-empty string")
    return mapping.get(channel, channel)


def _rx_groups(
    capture: dict[str, Any], mapping: dict[str, str], side: str
) -> tuple[dict[tuple[Any, ...], list[dict[str, Any]]], int]:
    frames = capture.get("frames")
    if not isinstance(frames, list):
        raise CanTraceComparisonError(f"{side} capture frames must be an array")
    if capture.get("frame_count") != len(frames):
        raise CanTraceComparisonError(f"{side} frame_count does not match frames length")

    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    ignored_tx = 0
    previous_time: int | None = None
    for index, frame in enumerate(frames):
        if not isinstance(frame, dict):
            raise CanTraceComparisonError(f"{side} frame {index} must be an object")
        direction = frame.get("direction")
        if direction == "Tx":
            ignored_tx += 1
            continue
        if direction != "Rx":
            raise CanTraceComparisonError(f"{side} frame {index} has unsupported direction")

        timestamp = frame.get("timestamp_ns")
        if isinstance(timestamp, bool) or not isinstance(timestamp, int) or timestamp < 0:
            raise CanTraceComparisonError(f"{side} frame {index} has invalid timestamp_ns")
        if previous_time is not None and timestamp < previous_time:
            raise CanTraceComparisonError(f"{side} capture timestamps regress")
        previous_time = timestamp

        arbitration_id = frame.get("arbitration_id")
        extended = frame.get("is_extended_id")
        remote = frame.get("is_remote_frame")
        dlc = frame.get("dlc")
        data_hex = frame.get("data_hex")
        if isinstance(arbitration_id, bool) or not isinstance(arbitration_id, int) or arbitration_id < 0:
            raise CanTraceComparisonError(f"{side} frame {index} has invalid arbitration_id")
        if extended not in (True, False) or remote not in (True, False):
            raise CanTraceComparisonError(f"{side} frame {index} has invalid frame flags")
        if isinstance(dlc, bool) or not isinstance(dlc, int) or dlc < 0:
            raise CanTraceComparisonError(f"{side} frame {index} has invalid DLC")
        if not isinstance(data_hex, str) or len(data_hex) % 2:
            raise CanTraceComparisonError(f"{side} frame {index} has invalid payload text")
        try:
            payload = bytes.fromhex(data_hex)
        except ValueError as exc:
            raise CanTraceComparisonError(f"{side} frame {index} has invalid payload hex") from exc
        if len(payload) != dlc:
            raise CanTraceComparisonError(f"{side} frame {index} has DLC/payload mismatch")

        key = (
            _logical_channel(frame.get("channel"), mapping, side),
            arbitration_id,
            extended,
            remote,
            dlc,
        )
        normalized = dict(frame)
        normalized["data_hex"] = payload.hex().upper()
        normalized["frame_index"] = index
        groups.setdefault(key, []).append(normalized)
    return groups, ignored_tx


def _example(kind: str, key: tuple[Any, ...], reference: Any, candidate: Any) -> dict[str, Any]:
    channel, arbitration_id, extended, remote, dlc = key
    return {
        "kind": kind,
        "logical_channel": channel,
        "arbitration_id": arbitration_id,
        "is_extended_id": extended,
        "is_remote_frame": remote,
        "dlc": dlc,
        "reference": reference,
        "candidate": candidate,
    }


def _trusted_timing(frames: list[dict[str, Any]]) -> bool:
    return bool(frames) and all(frame.get("timestamp_provenance") in TRUSTED_TIMING for frame in frames)


def compare_can_captures(
    reference: dict[str, Any],
    candidate: dict[str, Any],
    *,
    simultaneous: bool,
    reference_channel_map: dict[str, str] | None = None,
    candidate_channel_map: dict[str, str] | None = None,
    reference_quality_evidence: dict[str, Any] | None = None,
    max_examples: int = 20,
) -> CanTraceComparisonReport:
    """Compare two captures; the reference must independently qualify as full-rate."""
    if isinstance(max_examples, bool) or not isinstance(max_examples, int) or max_examples < 0:
        raise CanTraceComparisonError("max_examples must be a non-negative integer")
    if not isinstance(simultaneous, bool):
        raise CanTraceComparisonError("simultaneous must be true or false")

    reference_map = _validate_channel_map(reference_channel_map, "reference_channel_map")
    candidate_map = _validate_channel_map(candidate_channel_map, "candidate_channel_map")
    reference_groups, ignored_reference_tx = _rx_groups(reference, reference_map, "reference")
    candidate_groups, ignored_candidate_tx = _rx_groups(candidate, candidate_map, "candidate")

    # Import locally so this report type can also be consumed by the evaluator
    # without a module-import cycle.
    from validation.capture_quality_evaluator import evaluate_can_capture

    reference_quality = evaluate_can_capture(
        reference, supplemental_evidence=reference_quality_evidence
    ).evaluated_quality

    matched_pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    payload_mismatches = 0
    missing = 0
    extra = 0
    examples: list[dict[str, Any]] = []
    keys = sorted(set(reference_groups) | set(candidate_groups), key=repr)
    for key in keys:
        ref_frames = reference_groups.get(key, [])
        cand_frames = candidate_groups.get(key, [])
        ref_payloads = [frame["data_hex"] for frame in ref_frames]
        cand_payloads = [frame["data_hex"] for frame in cand_frames]
        matcher = SequenceMatcher(a=ref_payloads, b=cand_payloads, autojunk=False)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                matched_pairs.extend(zip(ref_frames[i1:i2], cand_frames[j1:j2]))
                continue
            if tag == "replace":
                paired = min(i2 - i1, j2 - j1)
                for offset in range(paired):
                    ref_frame = ref_frames[i1 + offset]
                    cand_frame = cand_frames[j1 + offset]
                    matched_pairs.append((ref_frame, cand_frame))
                    payload_mismatches += 1
                    if len(examples) < max_examples:
                        examples.append(_example("PAYLOAD_MISMATCH", key, ref_frame["data_hex"], cand_frame["data_hex"]))
                missing += (i2 - i1) - paired
                extra += (j2 - j1) - paired
            elif tag == "delete":
                missing += i2 - i1
            elif tag == "insert":
                extra += j2 - j1
            if tag in {"delete", "replace"} and len(examples) < max_examples and i2 - i1:
                examples.append(_example("MISSING" if tag == "delete" else "SEQUENCE_DIVERGENCE", key, ref_payloads[i1:i2], cand_payloads[j1:j2]))
            if tag == "insert" and len(examples) < max_examples:
                examples.append(_example("EXTRA", key, [], cand_payloads[j1:j2]))

    reference_rx_count = sum(map(len, reference_groups.values()))
    candidate_rx_count = sum(map(len, candidate_groups.values()))
    exact_payload_matches = len(matched_pairs) - payload_mismatches
    if not simultaneous:
        frame_fidelity = "NOT_SIMULTANEOUS"
    elif reference_quality != "FULL_RATE_CANDIDATE":
        frame_fidelity = "UNQUALIFIED_REFERENCE"
    elif reference_rx_count == 0:
        frame_fidelity = "INVALID"
    elif missing or extra or payload_mismatches or reference_rx_count != candidate_rx_count:
        frame_fidelity = "MISMATCH"
    else:
        frame_fidelity = "EXACT"

    ref_flat = [frame for frames in reference_groups.values() for frame in frames]
    cand_flat = [frame for frames in candidate_groups.values() for frame in frames]
    offset: int | None = None
    median_residual: int | None = None
    max_residual: int | None = None
    if _trusted_timing(ref_flat) and _trusted_timing(cand_flat) and matched_pairs:
        deltas = [cand["timestamp_ns"] - ref["timestamp_ns"] for ref, cand in matched_pairs]
        offset = int(median(deltas))
        residuals = [abs(delta - offset) for delta in deltas]
        median_residual = int(median(residuals))
        max_residual = max(residuals)
        timing_fidelity = "PER_FRAME_COMPARABLE"
    else:
        timing_fidelity = "TIMING_UNVERIFIED"

    report = CanTraceComparisonReport(
        candidate_capture_id=candidate.get("capture_id"),
        reference_capture_id=reference.get("capture_id"),
        simultaneous=simultaneous,
        reference_capture_quality=reference_quality,
        frame_fidelity=frame_fidelity,
        timing_fidelity=timing_fidelity,
        reference_rx_count=reference_rx_count,
        candidate_rx_count=candidate_rx_count,
        matched_frame_count=exact_payload_matches,
        payload_mismatch_count=payload_mismatches,
        missing_frame_count=missing,
        extra_frame_count=extra,
        ignored_reference_tx_count=ignored_reference_tx,
        ignored_candidate_tx_count=ignored_candidate_tx,
        clock_offset_ns=offset,
        median_absolute_timing_residual_ns=median_residual,
        max_absolute_timing_residual_ns=max_residual,
        mismatch_examples=examples[:max_examples],
    )
    report.validate()
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare simultaneous canonical CAN captures offline")
    parser.add_argument("reference", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--simultaneous", action="store_true", required=True)
    parser.add_argument("--reference-channel-map", type=Path)
    parser.add_argument("--candidate-channel-map", type=Path)
    parser.add_argument("--reference-quality-evidence", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    load = lambda path: json.loads(path.read_text(encoding="utf-8")) if path else None
    report = compare_can_captures(
        load(args.reference),
        load(args.candidate),
        simultaneous=args.simultaneous,
        reference_channel_map=load(args.reference_channel_map),
        candidate_channel_map=load(args.candidate_channel_map),
        reference_quality_evidence=load(args.reference_quality_evidence),
    )
    rendered = json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
