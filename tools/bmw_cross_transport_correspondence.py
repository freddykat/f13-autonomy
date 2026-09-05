#!/usr/bin/env python3
"""Offline CAN<->FlexRay correspondence analysis for BMW passive captures.

This stage compares already-discovered CAN and FlexRay function evidence against
one synchronized raw capture. It looks for temporally correlated raw fields of
the same function family without flattening FlexRay into fake CAN identities.

A strong match is still only a correspondence hypothesis. It does not prove
which ECU originated the signal, whether ZGW forwarded/derived it, or what the
engineering scale/unit is.
"""

from __future__ import annotations

import argparse
import bisect
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from tools.bmw_transport import BMWTransportFrame, load_transport_trace


@dataclass(frozen=True)
class EvidenceField:
    function_family: str
    function_kind: str
    transport: str
    source_key: str
    feature_kind: str
    start_byte: int
    width: int | None
    bit: int | None
    signed: bool | None
    endian: str | None
    evidence_score: float
    confidence: str
    bus: str | None = None
    address: int | None = None
    channel: str | None = None
    slot_id: int | None = None
    cycle: int | None = None
    base_cycle: int | None = None
    cycle_repetition: int | None = None
    frame_id: int | None = None


@dataclass(frozen=True)
class CrossTransportCorrespondence:
    function_family: str
    can_source_key: str
    flexray_source_key: str
    can_feature: str
    flexray_feature: str
    aligned_pairs: int
    can_samples: int
    flexray_samples: int
    overlap_score: float
    correlation: float
    absolute_correlation: float
    raw_polarity_relation: str
    best_lag_ms: float
    mean_abs_alignment_error_ms: float
    evidence_quality: float
    correspondence_score: float
    relationship: str
    gateway_hypothesis: str
    status: str = "UNVALIDATED_CROSS_TRANSPORT_CORRESPONDENCE"


def _optional_int(item: dict[str, Any], name: str) -> int | None:
    value = item.get(name)
    return None if value is None else int(value)


def _optional_bool(item: dict[str, Any], name: str) -> bool | None:
    value = item.get(name)
    return None if value is None else bool(value)


def _parse_evidence(item: dict[str, Any]) -> EvidenceField:
    return EvidenceField(
        function_family=str(item["function_family"]),
        function_kind=str(item["function_kind"]),
        transport=str(item["transport"]).upper(),
        source_key=str(item["source_key"]),
        feature_kind=str(item["feature_kind"]),
        start_byte=int(item["start_byte"]),
        width=_optional_int(item, "width"),
        bit=_optional_int(item, "bit"),
        signed=_optional_bool(item, "signed"),
        endian=None if item.get("endian") is None else str(item["endian"]),
        evidence_score=float(item.get("evidence_score", 0.0)),
        confidence=str(item.get("confidence", "LOW")),
        bus=None if item.get("bus") is None else str(item["bus"]),
        address=_optional_int(item, "address"),
        channel=None if item.get("channel") is None else str(item["channel"]),
        slot_id=_optional_int(item, "slot_id"),
        cycle=_optional_int(item, "cycle"),
        base_cycle=_optional_int(item, "base_cycle"),
        cycle_repetition=_optional_int(item, "cycle_repetition"),
        frame_id=_optional_int(item, "frame_id"),
    )


def load_evidence(path: Path) -> list[EvidenceField]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    items = payload.get("evidence")
    if not isinstance(items, list):
        raise ValueError(f"{path}: missing evidence list")
    return [_parse_evidence(item) for item in items]


def _matches(field: EvidenceField, frame: BMWTransportFrame) -> bool:
    identity = frame.identity
    if identity.transport != field.transport:
        return False

    if field.transport == "CAN":
        if field.address is not None and identity.address != field.address:
            return False
        if field.bus is not None and identity.bus != field.bus:
            return False
        return True

    if field.transport != "FLEXRAY":
        return False

    if field.channel is not None and identity.channel != field.channel:
        return False
    if field.slot_id is not None and identity.slot_id != field.slot_id:
        return False
    if field.frame_id is not None and identity.frame_id is not None and identity.frame_id != field.frame_id:
        return False

    # Prefer schedule identity when the evidence carries one. Raw captures may
    # know only the current cycle, so accept cycles belonging to that schedule.
    if field.base_cycle is not None:
        repetition = field.cycle_repetition
        if repetition is None or repetition <= 0:
            return False
        if identity.base_cycle is not None:
            if identity.base_cycle != field.base_cycle:
                return False
            if (
                identity.cycle_repetition is not None
                and identity.cycle_repetition != repetition
            ):
                return False
            return True
        if identity.cycle is None:
            return False
        return (identity.cycle - field.base_cycle) % repetition == 0

    if field.cycle is not None and identity.cycle != field.cycle:
        return False

    return True


def _decode(field: EvidenceField, data: bytes) -> float | None:
    if field.feature_kind == "bit":
        if field.bit is None or field.start_byte < 0 or field.start_byte >= len(data):
            return None
        if field.bit < 0 or field.bit > 7:
            return None
        return float((data[field.start_byte] >> field.bit) & 1)

    if field.feature_kind != "continuous_integer":
        return None
    if field.width is None or field.signed is None or field.endian is None:
        return None
    if field.width not in (1, 2, 3):
        return None

    end = field.start_byte + field.width
    if field.start_byte < 0 or end > len(data):
        return None
    return float(int.from_bytes(
        data[field.start_byte:end],
        byteorder=field.endian,
        signed=field.signed,
    ))


def _series(field: EvidenceField, frames: list[BMWTransportFrame]) -> list[tuple[float, float]]:
    values: list[tuple[float, float]] = []
    for frame in frames:
        if not _matches(field, frame):
            continue
        value = _decode(field, frame.data)
        if value is not None:
            values.append((frame.t, value))
    values.sort(key=lambda item: item[0])
    return values


def _pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 3:
        return 0.0
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    dx = [x - mean_x for x in xs]
    dy = [y - mean_y for y in ys]
    denom = math.sqrt(sum(x * x for x in dx) * sum(y * y for y in dy))
    if denom <= 1e-12:
        return 0.0
    return sum(x * y for x, y in zip(dx, dy)) / denom


def _align_unique(
    can_series: list[tuple[float, float]],
    flexray_series: list[tuple[float, float]],
    *,
    lag_s: float,
    tolerance_s: float,
) -> tuple[list[tuple[float, float]], list[float]]:
    """Greedily align each sample of the shorter stream to one unique peer."""
    if not can_series or not flexray_series:
        return [], []

    if len(can_series) <= len(flexray_series):
        anchor = can_series
        peer = flexray_series
        anchor_is_can = True
        peer_times = [t + lag_s for t, _ in peer]
    else:
        anchor = flexray_series
        peer = can_series
        anchor_is_can = False
        # If anchoring on FlexRay, compare shifted FlexRay time to CAN times.
        peer_times = [t for t, _ in peer]

    used: set[int] = set()
    pairs: list[tuple[float, float]] = []
    errors: list[float] = []

    for anchor_t, anchor_value in anchor:
        target_t = anchor_t if anchor_is_can else anchor_t + lag_s
        idx = bisect.bisect_left(peer_times, target_t)
        candidates = []
        for candidate_idx in (idx - 1, idx, idx + 1):
            if 0 <= candidate_idx < len(peer) and candidate_idx not in used:
                peer_t = peer_times[candidate_idx]
                candidates.append((abs(peer_t - target_t), candidate_idx))
        if not candidates:
            continue

        error, best_idx = min(candidates)
        if error > tolerance_s:
            continue

        used.add(best_idx)
        peer_value = peer[best_idx][1]
        if anchor_is_can:
            pairs.append((anchor_value, peer_value))
        else:
            pairs.append((peer_value, anchor_value))
        errors.append(error)

    return pairs, errors


def _lag_candidates(max_lag_ms: int, lag_step_ms: int) -> list[int]:
    if max_lag_ms < 0:
        raise ValueError("max_lag_ms must be non-negative")
    if lag_step_ms <= 0:
        raise ValueError("lag_step_ms must be positive")
    values = list(range(-max_lag_ms, max_lag_ms + 1, lag_step_ms))
    if 0 not in values:
        values.append(0)
    return sorted(set(values))


def _feature_label(field: EvidenceField) -> str:
    if field.feature_kind == "bit":
        return f"byte{field.start_byte}.bit{field.bit}"
    signed = "s" if field.signed else "u"
    endian = "be" if field.endian == "big" else "le"
    return f"byte{field.start_byte}:{field.width}:{signed}:{endian}"


def _classify(
    *,
    pairs: int,
    absolute_correlation: float,
    overlap_score: float,
    evidence_quality: float,
) -> tuple[str, str]:
    if (
        pairs >= 5
        and absolute_correlation >= 0.95
        and overlap_score >= 0.60
        and evidence_quality >= 0.75
    ):
        return (
            "STRONG_DUAL_TRANSPORT_CORRESPONDENCE",
            "POSSIBLE_ZGW_FORWARD_OR_DERIVED_REPRESENTATION",
        )
    if (
        pairs >= 4
        and absolute_correlation >= 0.80
        and overlap_score >= 0.40
        and evidence_quality >= 0.60
    ):
        return (
            "POSSIBLE_DUAL_TRANSPORT_CORRESPONDENCE",
            "NOT_INFERRED",
        )
    return ("WEAK_OR_UNRELATED", "NOT_INFERRED")


def rank_cross_transport_correspondence(
    frames: list[BMWTransportFrame],
    evidence: list[EvidenceField],
    *,
    minimum_evidence_score: float = 0.60,
    max_lag_ms: int = 100,
    lag_step_ms: int = 5,
    alignment_tolerance_ms: float = 25.0,
) -> list[CrossTransportCorrespondence]:
    """Compare CAN/FlexRay evidence pairs of the same function family."""
    can_fields = [
        item for item in evidence
        if item.transport == "CAN" and item.evidence_score >= minimum_evidence_score
    ]
    flex_fields = [
        item for item in evidence
        if item.transport == "FLEXRAY" and item.evidence_score >= minimum_evidence_score
    ]

    series_cache: dict[EvidenceField, list[tuple[float, float]]] = {}
    for field in can_fields + flex_fields:
        series_cache[field] = _series(field, frames)

    ranked: list[CrossTransportCorrespondence] = []
    tolerance_s = alignment_tolerance_ms / 1000.0

    for can_field in can_fields:
        for flex_field in flex_fields:
            if can_field.function_family != flex_field.function_family:
                continue
            can_series = series_cache[can_field]
            flex_series = series_cache[flex_field]
            if len(can_series) < 3 or len(flex_series) < 3:
                continue

            best: tuple[float, int, float, list[tuple[float, float]], list[float]] | None = None
            for lag_ms in _lag_candidates(max_lag_ms, lag_step_ms):
                pairs, errors = _align_unique(
                    can_series,
                    flex_series,
                    lag_s=lag_ms / 1000.0,
                    tolerance_s=tolerance_s,
                )
                if len(pairs) < 3:
                    continue
                can_values = [pair[0] for pair in pairs]
                flex_values = [pair[1] for pair in pairs]
                correlation = _pearson(can_values, flex_values)
                overlap = len(pairs) / float(min(len(can_series), len(flex_series)))
                lag_rank_score = abs(correlation) * overlap
                candidate = (lag_rank_score, lag_ms, correlation, pairs, errors)
                if best is None or candidate[0] > best[0]:
                    best = candidate

            if best is None:
                continue

            _, best_lag_ms, correlation, pairs, errors = best
            absolute_correlation = abs(correlation)
            overlap_score = len(pairs) / float(min(len(can_series), len(flex_series)))
            evidence_quality = 0.5 * (
                can_field.evidence_score + flex_field.evidence_score
            )
            correspondence_score = (
                0.65 * absolute_correlation
                + 0.20 * overlap_score
                + 0.15 * evidence_quality
            )
            relationship, gateway_hypothesis = _classify(
                pairs=len(pairs),
                absolute_correlation=absolute_correlation,
                overlap_score=overlap_score,
                evidence_quality=evidence_quality,
            )

            if correlation > 0.05:
                polarity_relation = "SAME_RAW_POLARITY"
            elif correlation < -0.05:
                polarity_relation = "INVERTED_RAW_POLARITY"
            else:
                polarity_relation = "UNRESOLVED"

            ranked.append(CrossTransportCorrespondence(
                function_family=can_field.function_family,
                can_source_key=can_field.source_key,
                flexray_source_key=flex_field.source_key,
                can_feature=_feature_label(can_field),
                flexray_feature=_feature_label(flex_field),
                aligned_pairs=len(pairs),
                can_samples=len(can_series),
                flexray_samples=len(flex_series),
                overlap_score=overlap_score,
                correlation=correlation,
                absolute_correlation=absolute_correlation,
                raw_polarity_relation=polarity_relation,
                best_lag_ms=float(best_lag_ms),
                mean_abs_alignment_error_ms=(
                    1000.0 * sum(errors) / len(errors) if errors else math.inf
                ),
                evidence_quality=evidence_quality,
                correspondence_score=correspondence_score,
                relationship=relationship,
                gateway_hypothesis=gateway_hypothesis,
            ))

    ranked.sort(key=lambda item: (
        -item.correspondence_score,
        -item.absolute_correlation,
        -item.overlap_score,
        item.function_family,
        item.can_source_key,
        item.flexray_source_key,
    ))
    return ranked


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare passive BMW CAN/FlexRay function evidence in a synchronized trace"
    )
    parser.add_argument("trace", type=Path)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--minimum-evidence-score", type=float, default=0.60)
    parser.add_argument("--max-lag-ms", type=int, default=100)
    parser.add_argument("--lag-step-ms", type=int, default=5)
    parser.add_argument("--alignment-tolerance-ms", type=float, default=25.0)
    parser.add_argument("--top", type=int, default=100)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    ranked = rank_cross_transport_correspondence(
        load_transport_trace(args.trace),
        load_evidence(args.evidence),
        minimum_evidence_score=args.minimum_evidence_score,
        max_lag_ms=args.max_lag_ms,
        lag_step_ms=args.lag_step_ms,
        alignment_tolerance_ms=args.alignment_tolerance_ms,
    )
    payload = {
        "mode": "OFFLINE_READ_ONLY_CROSS_TRANSPORT_CORRELATION",
        "status": "UNVALIDATED_CROSS_TRANSPORT_CORRESPONDENCE",
        "gateway_derivation_proven": False,
        "auto_promote": False,
        "decoder_generation": False,
        "diagnostic_writes": False,
        "transmit": False,
        "actuation_authority": "NONE",
        "correspondence": [asdict(item) for item in ranked[: args.top]],
    }
    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
