#!/usr/bin/env python3
"""Offline transport-aware BMW function hypothesis identifier.

The identifier ranks raw CAN/FlexRay features against user-defined event
signatures. It outputs hypotheses such as STEERING_LIKE or LEAD_RANGE_LIKE.
It never creates decoders, engineering units, DBCs, diagnostic writes,
transmit paths, or control authority.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from tools.bmw_signal_correlation import Marker, load_markers
from tools.bmw_transport import BMWTransportFrame, TransportIdentity, load_transport_trace


@dataclass(frozen=True)
class FunctionSpec:
    name: str
    kind: str
    positive_event: str
    negative_event: str
    baseline_event: str | None = None


@dataclass(frozen=True)
class FunctionHypothesis:
    function_family: str
    function_kind: str
    transport: str
    source_key: str
    bus: str | None
    address: int | None
    channel: str | None
    slot_id: int | None
    cycle: int | None
    base_cycle: int | None
    cycle_repetition: int | None
    frame_id: int | None
    feature_kind: str
    start_byte: int
    width: int | None
    bit: int | None
    signed: bool | None
    endian: str | None
    score: float
    direction_score: float
    baseline_score: float
    transition_strength: float
    coverage_score: float
    positive_observations: int
    negative_observations: int
    baseline_observations: int
    raw_polarity: str
    status: str = "UNVALIDATED_FUNCTION_HYPOTHESIS"


def load_function_specs(path: Path) -> list[FunctionSpec]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    raw_specs = obj.get("functions", obj)
    if not isinstance(raw_specs, list):
        raise ValueError("function signature file must contain a list or {'functions': [...]}")

    specs: list[FunctionSpec] = []
    for item in raw_specs:
        spec = FunctionSpec(
            name=str(item["name"]),
            kind=str(item["kind"]),
            positive_event=str(item["positive_event"]),
            negative_event=str(item["negative_event"]),
            baseline_event=None if item.get("baseline_event") is None else str(item["baseline_event"]),
        )
        if spec.kind not in {"opposed_continuous", "toggle"}:
            raise ValueError(f"unsupported function kind: {spec.kind}")
        specs.append(spec)
    return specs


def _window(frames: Iterable[BMWTransportFrame], start: float, end: float):
    for frame in frames:
        if start <= frame.t < end:
            yield frame


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else math.nan


def _source_key(identity: TransportIdentity) -> tuple[Any, ...]:
    return identity.correlation_key()


def _source_key_text(key: tuple[Any, ...]) -> str:
    return "|".join("None" if value is None else str(value) for value in key)


def _decode(raw: bytes, start: int, width: int, signed: bool, endian: str) -> int | None:
    end = start + width
    if start < 0 or end > len(raw):
        return None
    return int.from_bytes(raw[start:end], byteorder=endian, signed=signed)


def _continuous_values(
    frames: Iterable[BMWTransportFrame],
    widths: tuple[int, ...],
) -> tuple[dict[tuple, list[float]], dict[tuple, TransportIdentity]]:
    grouped: dict[tuple, list[float]] = defaultdict(list)
    sources: dict[tuple, TransportIdentity] = {}

    for frame in frames:
        source = _source_key(frame.identity)
        sources[source] = frame.identity
        for width in widths:
            if width not in (1, 2, 3):
                raise ValueError("widths must contain only 1, 2, or 3")
            endians = ("big",) if width == 1 else ("big", "little")
            for signed in (False, True):
                for endian in endians:
                    for start in range(0, len(frame.data) - width + 1):
                        value = _decode(frame.data, start, width, signed, endian)
                        if value is not None:
                            grouped[(source, start, width, signed, endian)].append(float(value))
    return grouped, sources


def _bit_values(
    frames: Iterable[BMWTransportFrame],
) -> tuple[dict[tuple, list[float]], dict[tuple, TransportIdentity]]:
    grouped: dict[tuple, list[float]] = defaultdict(list)
    sources: dict[tuple, TransportIdentity] = {}

    for frame in frames:
        source = _source_key(frame.identity)
        sources[source] = frame.identity
        for byte_idx, value in enumerate(frame.data):
            for bit in range(8):
                grouped[(source, byte_idx, bit)].append(float((value >> bit) & 1))
    return grouped, sources


def _collect_observations(
    frames: list[BMWTransportFrame],
    markers: list[Marker],
    *,
    before_s: float,
    after_s: float,
    widths: tuple[int, ...],
):
    continuous: dict[tuple, list[tuple[float, float, float]]] = defaultdict(list)
    bits: dict[tuple, list[tuple[float, float, float]]] = defaultdict(list)
    representatives: dict[tuple, TransportIdentity] = {}

    for marker in markers:
        before = list(_window(frames, marker.t - before_s, marker.t))
        after = list(_window(frames, marker.t, marker.t + after_s))

        bcont, bsources = _continuous_values(before, widths)
        acont, asources = _continuous_values(after, widths)
        representatives.update(bsources)
        representatives.update(asources)

        for feature in set(bcont) & set(acont):
            bmean = _mean(bcont[feature])
            amean = _mean(acont[feature])
            continuous[(marker.event,) + feature].append((bmean, amean, amean - bmean))

        bbits, bsources = _bit_values(before)
        abits, asources = _bit_values(after)
        representatives.update(bsources)
        representatives.update(asources)

        for feature in set(bbits) & set(abits):
            bmean = _mean(bbits[feature])
            amean = _mean(abits[feature])
            bits[(marker.event,) + feature].append((bmean, amean, amean - bmean))

    return continuous, bits, representatives


def _sign_fraction(deltas: list[float], expected_sign: int) -> float:
    nonzero = [delta for delta in deltas if abs(delta) > 1e-12]
    if not nonzero:
        return 0.0
    if expected_sign > 0:
        return sum(delta > 0 for delta in nonzero) / len(nonzero)
    return sum(delta < 0 for delta in nonzero) / len(nonzero)


def _coverage(
    positive: list[tuple[float, float, float]],
    negative: list[tuple[float, float, float]],
    baseline: list[tuple[float, float, float]],
    baseline_required: bool,
    min_observations: int,
) -> float:
    counts = [len(positive), len(negative)]
    if baseline_required:
        counts.append(len(baseline))
    repeatability = min(1.0, min(counts) / float(min_observations))
    return repeatability


def _hypothesis(
    spec: FunctionSpec,
    identity: TransportIdentity,
    source: tuple[Any, ...],
    *,
    feature_kind: str,
    start_byte: int,
    width: int | None,
    bit: int | None,
    signed: bool | None,
    endian: str | None,
    score: float,
    direction_score: float,
    baseline_score: float,
    transition_strength: float,
    coverage_score: float,
    positive_observations: int,
    negative_observations: int,
    baseline_observations: int,
    raw_polarity: str,
) -> FunctionHypothesis:
    return FunctionHypothesis(
        function_family=spec.name,
        function_kind=spec.kind,
        transport=identity.transport,
        source_key=_source_key_text(source),
        bus=identity.bus,
        address=identity.address,
        channel=identity.channel,
        slot_id=identity.slot_id,
        cycle=identity.cycle,
        base_cycle=identity.base_cycle,
        cycle_repetition=identity.cycle_repetition,
        frame_id=identity.frame_id,
        feature_kind=feature_kind,
        start_byte=start_byte,
        width=width,
        bit=bit,
        signed=signed,
        endian=endian,
        score=score,
        direction_score=direction_score,
        baseline_score=baseline_score,
        transition_strength=transition_strength,
        coverage_score=coverage_score,
        positive_observations=positive_observations,
        negative_observations=negative_observations,
        baseline_observations=baseline_observations,
        raw_polarity=raw_polarity,
    )


def identify_function_hypotheses(
    frames: list[BMWTransportFrame],
    markers: list[Marker],
    specs: list[FunctionSpec],
    *,
    before_s: float = 1.0,
    after_s: float = 1.0,
    min_observations: int = 2,
    widths: tuple[int, ...] = (1, 2, 3),
) -> list[FunctionHypothesis]:
    """Rank raw CAN/FlexRay features against event-signature function families."""
    continuous, bits, representatives = _collect_observations(
        frames,
        markers,
        before_s=before_s,
        after_s=after_s,
        widths=widths,
    )
    ranked: list[FunctionHypothesis] = []

    for spec in specs:
        observations = continuous if spec.kind == "opposed_continuous" else bits
        feature_keys: set[tuple] = set()
        relevant_events = {spec.positive_event, spec.negative_event}
        if spec.baseline_event:
            relevant_events.add(spec.baseline_event)

        for key in observations:
            event, *feature = key
            if event in relevant_events:
                feature_keys.add(tuple(feature))

        for feature in feature_keys:
            source = feature[0]
            positive = observations.get((spec.positive_event,) + feature, [])
            negative = observations.get((spec.negative_event,) + feature, [])
            baseline = (
                observations.get((spec.baseline_event,) + feature, [])
                if spec.baseline_event
                else []
            )

            if len(positive) < min_observations or len(negative) < min_observations:
                continue
            if spec.baseline_event and len(baseline) < min_observations:
                continue

            pos_deltas = [item[2] for item in positive]
            neg_deltas = [item[2] for item in negative]
            assignment_a = 0.5 * (
                _sign_fraction(pos_deltas, +1) + _sign_fraction(neg_deltas, -1)
            )
            assignment_b = 0.5 * (
                _sign_fraction(pos_deltas, -1) + _sign_fraction(neg_deltas, +1)
            )
            if assignment_a >= assignment_b:
                direction_score = assignment_a
                raw_polarity = "positive_event_raw_positive"
            else:
                direction_score = assignment_b
                raw_polarity = "positive_event_raw_negative"

            coverage_score = _coverage(
                positive,
                negative,
                baseline,
                spec.baseline_event is not None,
                min_observations,
            )

            if spec.kind == "opposed_continuous":
                _, start_byte, width, signed, endian = feature
                baseline_score = 1.0
                if spec.baseline_event:
                    positive_after = _mean([item[1] for item in positive])
                    negative_after = _mean([item[1] for item in negative])
                    baseline_after = _mean([item[1] for item in baseline])
                    midpoint = 0.5 * (positive_after + negative_after)
                    separation = abs(positive_after - negative_after)
                    baseline_score = (
                        0.0
                        if separation <= 1e-12
                        else max(0.0, 1.0 - abs(baseline_after - midpoint) / separation)
                    )

                bits_count = int(width) * 8
                numeric_span = float((1 << bits_count) - 1)
                transition_strength = min(
                    1.0,
                    (
                        abs(_mean(pos_deltas))
                        + abs(_mean(neg_deltas))
                    )
                    / (2.0 * numeric_span),
                )
                score = (
                    0.60 * direction_score
                    + 0.25 * baseline_score
                    + 0.10 * coverage_score
                    + 0.05 * transition_strength
                )
                ranked.append(_hypothesis(
                    spec,
                    representatives[source],
                    source,
                    feature_kind="continuous_integer",
                    start_byte=int(start_byte),
                    width=int(width),
                    bit=None,
                    signed=bool(signed),
                    endian=str(endian),
                    score=score,
                    direction_score=direction_score,
                    baseline_score=baseline_score,
                    transition_strength=transition_strength,
                    coverage_score=coverage_score,
                    positive_observations=len(positive),
                    negative_observations=len(negative),
                    baseline_observations=len(baseline),
                    raw_polarity=raw_polarity,
                ))
            else:
                _, byte_idx, bit = feature
                baseline_score = 1.0
                transition_strength = min(
                    1.0,
                    0.5 * (
                        abs(_mean(pos_deltas))
                        + abs(_mean(neg_deltas))
                    ),
                )
                score = (
                    0.65 * direction_score
                    + 0.25 * transition_strength
                    + 0.10 * coverage_score
                )
                ranked.append(_hypothesis(
                    spec,
                    representatives[source],
                    source,
                    feature_kind="bit",
                    start_byte=int(byte_idx),
                    width=None,
                    bit=int(bit),
                    signed=None,
                    endian=None,
                    score=score,
                    direction_score=direction_score,
                    baseline_score=baseline_score,
                    transition_strength=transition_strength,
                    coverage_score=coverage_score,
                    positive_observations=len(positive),
                    negative_observations=len(negative),
                    baseline_observations=len(baseline),
                    raw_polarity=raw_polarity,
                ))

    ranked.sort(key=lambda item: (
        -item.score,
        -item.direction_score,
        -item.coverage_score,
        item.function_family,
        item.transport,
        item.source_key,
        item.start_byte,
        -1 if item.bit is None else item.bit,
        -1 if item.width is None else item.width,
    ))
    return ranked


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Rank passive BMW CAN/FlexRay features against function signatures"
    )
    parser.add_argument("trace", type=Path)
    parser.add_argument("markers", type=Path)
    parser.add_argument(
        "--signatures",
        type=Path,
        default=Path("validation/manifests/prototype_001_bmw_function_signatures.json"),
    )
    parser.add_argument("--before", type=float, default=1.0)
    parser.add_argument("--after", type=float, default=1.0)
    parser.add_argument("--min-observations", type=int, default=2)
    parser.add_argument("--top", type=int, default=100)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    hypotheses = identify_function_hypotheses(
        load_transport_trace(args.trace),
        load_markers(args.markers),
        load_function_specs(args.signatures),
        before_s=args.before,
        after_s=args.after,
        min_observations=args.min_observations,
    )
    payload = {
        "mode": "OFFLINE_READ_ONLY_DISCOVERY",
        "transport_policy": "PRESERVE_CAN_AND_FLEXRAY_PROVENANCE",
        "status": "UNVALIDATED_FUNCTION_HYPOTHESES",
        "auto_promote": False,
        "decoder_generation": False,
        "diagnostic_writes": False,
        "transmit": False,
        "actuation_authority": "NONE",
        "hypotheses": [asdict(item) for item in hypotheses[: args.top]],
    }
    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
