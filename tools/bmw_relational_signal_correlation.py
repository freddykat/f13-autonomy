#!/usr/bin/env python3
"""Cross-event correlation for BMW passive traces.

This module evaluates whether the same raw integer interpretation behaves
coherently across complementary event markers (for example left/right/center).
It is strictly offline/read-only discovery logic and does not assign semantics,
engineering units, decoder authority, or control capability.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

from tools.bmw_signal_correlation import Frame, Marker


@dataclass(frozen=True)
class RelationSpec:
    name: str
    positive_event: str
    negative_event: str
    baseline_event: str | None = None


@dataclass(frozen=True)
class RelationalCandidate:
    relation: str
    bus: str
    address: int
    start_byte: int
    width: int
    signed: bool
    endian: str
    score: float
    positive_observations: int
    negative_observations: int
    baseline_observations: int
    positive_mean_delta: float
    negative_mean_delta: float
    opposite_direction_score: float
    baseline_recovery_score: float
    coverage_score: float
    kind: str = "relational_continuous_integer"


def _decode(raw: bytes, start: int, width: int, signed: bool, endian: str) -> int | None:
    end = start + width
    if start < 0 or end > len(raw):
        return None
    return int.from_bytes(raw[start:end], byteorder=endian, signed=signed)


def _window(frames: Iterable[Frame], start: float, end: float):
    for frame in frames:
        if start <= frame.t < end:
            yield frame


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else math.nan


def _group_values(frames: Iterable[Frame], width: int, signed: bool, endian: str):
    grouped: dict[tuple[str, int, int], list[float]] = defaultdict(list)
    for frame in frames:
        for start in range(0, len(frame.data) - width + 1):
            value = _decode(frame.data, start, width, signed, endian)
            if value is not None:
                grouped[(frame.bus, frame.address, start)].append(float(value))
    return grouped


def _collect_event_observations(
    frames: list[Frame],
    markers: list[Marker],
    *,
    before_s: float,
    after_s: float,
    widths: tuple[int, ...],
):
    # key: (event, bus, address, start_byte, width, signed, endian)
    # value: list[(before_mean, after_mean, delta)]
    observations: dict[tuple, list[tuple[float, float, float]]] = defaultdict(list)

    for width in widths:
        if width not in (1, 2, 3):
            raise ValueError("widths must contain only 1, 2, or 3")

    for marker in markers:
        before = list(_window(frames, marker.t - before_s, marker.t))
        after = list(_window(frames, marker.t, marker.t + after_s))
        for width in widths:
            endians = ("big",) if width == 1 else ("big", "little")
            for signed in (False, True):
                for endian in endians:
                    bvals = _group_values(before, width, signed, endian)
                    avals = _group_values(after, width, signed, endian)
                    for (bus, address, start_byte) in set(bvals) & set(avals):
                        bmean = _mean(bvals[(bus, address, start_byte)])
                        amean = _mean(avals[(bus, address, start_byte)])
                        observations[(
                            marker.event,
                            bus,
                            address,
                            start_byte,
                            width,
                            signed,
                            endian,
                        )].append((bmean, amean, amean - bmean))
    return observations


def _dominant_sign_fraction(deltas: list[float], expected_sign: int) -> float:
    nonzero = [d for d in deltas if abs(d) > 1e-12]
    if not nonzero:
        return 0.0
    if expected_sign > 0:
        return sum(d > 0 for d in nonzero) / len(nonzero)
    return sum(d < 0 for d in nonzero) / len(nonzero)


def rank_relational_candidates(
    frames: list[Frame],
    markers: list[Marker],
    relations: list[RelationSpec],
    *,
    before_s: float = 1.0,
    after_s: float = 1.0,
    min_observations: int = 2,
    widths: tuple[int, ...] = (1, 2, 3),
) -> list[RelationalCandidate]:
    """Rank raw integer interpretations using complementary event behavior.

    A relation requires a positive event and a negative event. The strongest
    candidates move consistently in opposite directions for those events. If a
    baseline event is provided, its post-event value is expected to return near
    the midpoint of the positive/negative post-event values.

    Scores are discovery evidence only. This function intentionally performs no
    semantic naming, scaling, DBC generation, decoder promotion, or transmission.
    """
    obs = _collect_event_observations(
        frames,
        markers,
        before_s=before_s,
        after_s=after_s,
        widths=widths,
    )

    ranked: list[RelationalCandidate] = []

    for relation in relations:
        feature_keys: set[tuple] = set()
        for key in obs:
            event, *feature = key
            if event in {relation.positive_event, relation.negative_event, relation.baseline_event}:
                feature_keys.add(tuple(feature))

        for feature in feature_keys:
            bus, address, start_byte, width, signed, endian = feature
            pos = obs.get((relation.positive_event,) + feature, [])
            neg = obs.get((relation.negative_event,) + feature, [])
            base = obs.get((relation.baseline_event,) + feature, []) if relation.baseline_event else []

            if len(pos) < min_observations or len(neg) < min_observations:
                continue
            if relation.baseline_event and len(base) < min_observations:
                continue

            pos_deltas = [x[2] for x in pos]
            neg_deltas = [x[2] for x in neg]
            pos_mean_delta = _mean(pos_deltas)
            neg_mean_delta = _mean(neg_deltas)

            # Do not assume which raw sign corresponds to left/right or closing/
            # opening. Score the better of the two opposite-sign assignments.
            assignment_a = 0.5 * (
                _dominant_sign_fraction(pos_deltas, +1)
                + _dominant_sign_fraction(neg_deltas, -1)
            )
            assignment_b = 0.5 * (
                _dominant_sign_fraction(pos_deltas, -1)
                + _dominant_sign_fraction(neg_deltas, +1)
            )
            opposite_direction_score = max(assignment_a, assignment_b)

            baseline_recovery_score = 1.0
            if relation.baseline_event:
                pos_after = _mean([x[1] for x in pos])
                neg_after = _mean([x[1] for x in neg])
                base_after = _mean([x[1] for x in base])
                midpoint = 0.5 * (pos_after + neg_after)
                separation = abs(pos_after - neg_after)
                if separation <= 1e-12:
                    baseline_recovery_score = 0.0
                else:
                    error = abs(base_after - midpoint)
                    baseline_recovery_score = max(0.0, 1.0 - error / separation)

            required_events = 3 if relation.baseline_event else 2
            observed_events = 2 + (1 if relation.baseline_event and base else 0)
            repeatability = min(
                1.0,
                min(len(pos), len(neg), len(base) if relation.baseline_event else min_observations)
                / float(min_observations),
            )
            coverage_score = (observed_events / required_events) * repeatability

            # Cross-event direction is the primary evidence. Baseline recovery
            # matters strongly when present, while coverage prevents one-off hits.
            score = (
                0.60 * opposite_direction_score
                + 0.25 * baseline_recovery_score
                + 0.15 * coverage_score
            )

            ranked.append(RelationalCandidate(
                relation=relation.name,
                bus=bus,
                address=address,
                start_byte=start_byte,
                width=width,
                signed=signed,
                endian=endian,
                score=score,
                positive_observations=len(pos),
                negative_observations=len(neg),
                baseline_observations=len(base),
                positive_mean_delta=pos_mean_delta,
                negative_mean_delta=neg_mean_delta,
                opposite_direction_score=opposite_direction_score,
                baseline_recovery_score=baseline_recovery_score,
                coverage_score=coverage_score,
            ))

    ranked.sort(key=lambda c: (
        -c.score,
        -c.opposite_direction_score,
        -c.baseline_recovery_score,
        -c.coverage_score,
        c.relation,
        c.bus,
        c.address,
        c.start_byte,
        c.width,
        c.signed,
        c.endian,
    ))
    return ranked
