#!/usr/bin/env python3
"""Offline continuous-signal discovery for BMW passive traces.

This module tries raw 1/2/3-byte integer interpretations without assigning
semantics, units, scale, bus ownership, or decoder authority. It is intended for
replay/capture research only.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

from tools.bmw_signal_correlation import Frame, Marker


@dataclass(frozen=True)
class ContinuousCandidate:
    event: str
    bus: str
    address: int
    start_byte: int
    width: int
    signed: bool
    endian: str
    score: float
    observations: int
    mean_delta: float
    sign_consistency: float
    direction_match: float
    kind: str = "continuous_integer"


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


def rank_continuous_candidates(
    frames: list[Frame],
    markers: list[Marker],
    *,
    before_s: float = 1.0,
    after_s: float = 1.0,
    min_observations: int = 2,
    expected_direction: dict[str, int] | None = None,
    widths: tuple[int, ...] = (1, 2, 3),
) -> list[ContinuousCandidate]:
    """Rank raw integer interpretations around repeated event markers.

    expected_direction maps event names to +1 / -1 / 0. A non-zero value means
    "prefer interpretations whose repeated before->after delta has this sign".
    Zero or missing values do not impose semantics.

    The score is heuristic discovery evidence only. It intentionally avoids
    converting raw integers to engineering units or producing decoder entries.
    """
    expected_direction = expected_direction or {}
    per_feature: dict[tuple, list[float]] = defaultdict(list)

    for marker in markers:
        before = list(_window(frames, marker.t - before_s, marker.t))
        after = list(_window(frames, marker.t, marker.t + after_s))
        for width in widths:
            if width not in (1, 2, 3):
                raise ValueError("widths must contain only 1, 2, or 3")
            endians = ("big",) if width == 1 else ("big", "little")
            for signed in (False, True):
                for endian in endians:
                    bvals = _group_values(before, width, signed, endian)
                    avals = _group_values(after, width, signed, endian)
                    for key in set(bvals) & set(avals):
                        delta = _mean(avals[key]) - _mean(bvals[key])
                        per_feature[(marker.event, width, signed, endian) + key].append(delta)

    ranked: list[ContinuousCandidate] = []
    for key, deltas in per_feature.items():
        if len(deltas) < min_observations:
            continue
        event, width, signed, endian, bus, address, start_byte = key
        nonzero = [d for d in deltas if abs(d) > 1e-12]
        if not nonzero:
            continue

        pos = sum(d > 0 for d in nonzero)
        neg = sum(d < 0 for d in nonzero)
        sign_consistency = max(pos, neg) / len(nonzero)
        mean_delta = sum(deltas) / len(deltas)

        direction = expected_direction.get(event, 0)
        if direction == 0:
            direction_match = 1.0
        else:
            matches = sum((d > 0 and direction > 0) or (d < 0 and direction < 0) for d in nonzero)
            direction_match = matches / len(nonzero)

        # Magnitude is normalized against the representable numeric range so
        # unlike widths can be compared without pretending to know signal scale.
        bits = width * 8
        numeric_span = float((1 << bits) - 1)
        magnitude = min(1.0, abs(mean_delta) / numeric_span)
        repeatability = min(1.0, len(deltas) / max(2.0, float(min_observations)))
        score = (0.50 * sign_consistency + 0.35 * direction_match + 0.15 * magnitude) * repeatability

        ranked.append(ContinuousCandidate(
            event=event,
            bus=bus,
            address=address,
            start_byte=start_byte,
            width=width,
            signed=signed,
            endian=endian,
            score=score,
            observations=len(deltas),
            mean_delta=mean_delta,
            sign_consistency=sign_consistency,
            direction_match=direction_match,
        ))

    ranked.sort(key=lambda c: (
        -c.score,
        -c.observations,
        c.event,
        c.bus,
        c.address,
        c.start_byte,
        c.width,
        c.signed,
        c.endian,
    ))
    return ranked
