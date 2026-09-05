#!/usr/bin/env python3
"""Offline pairing of BMW FRR raw range-like and relative-velocity-like fields.

This module works only on passive replay/capture data. It does not assign units,
DBC semantics, track authority, or any control meaning. The goal is to rank pairs
whose temporal behavior is physically self-consistent enough to deserve manual
review during BMW FRR decoder discovery.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

from tools.bmw_signal_correlation import Frame


@dataclass(frozen=True)
class RawField:
    bus: str
    address: int
    start_byte: int
    width: int
    signed: bool
    endian: str


@dataclass(frozen=True)
class TrackFieldPairCandidate:
    range_field: RawField
    velocity_field: RawField
    score: float
    samples: int
    derivative_sign_agreement: float
    correlation_abs: float
    steady_consistency: float
    same_bus: bool
    kind: str = "frr_range_velocity_pair"
    mode: str = "OFFLINE_READ_ONLY_DISCOVERY"
    auto_promote: bool = False
    actuation: str = "NONE"


def _decode(raw: bytes, field: RawField) -> float | None:
    end = field.start_byte + field.width
    if field.start_byte < 0 or end > len(raw):
        return None
    if field.width not in (1, 2, 3):
        raise ValueError("field width must be 1, 2, or 3 bytes")
    if field.endian not in ("big", "little"):
        raise ValueError("endian must be 'big' or 'little'")
    return float(int.from_bytes(raw[field.start_byte:end], byteorder=field.endian, signed=field.signed))


def _series(frames: Iterable[Frame], field: RawField) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    for frame in frames:
        if frame.bus != field.bus or frame.address != field.address:
            continue
        value = _decode(frame.data, field)
        if value is not None:
            out.append((frame.t, value))
    out.sort(key=lambda p: p[0])
    return out


def _nearest(series: list[tuple[float, float]], t: float, max_dt: float) -> float | None:
    best: tuple[float, float] | None = None
    for ts, value in series:
        dt = abs(ts - t)
        if dt <= max_dt and (best is None or dt < best[0]):
            best = (dt, value)
    return None if best is None else best[1]


def _pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 2 or len(xs) != len(ys):
        return 0.0
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    dx = [x - mx for x in xs]
    dy = [y - my for y in ys]
    denom = math.sqrt(sum(x * x for x in dx) * sum(y * y for y in dy))
    if denom <= 1e-12:
        return 0.0
    return sum(x * y for x, y in zip(dx, dy)) / denom


def score_range_velocity_pair(
    frames: list[Frame],
    range_field: RawField,
    velocity_field: RawField,
    *,
    max_pair_dt: float = 0.08,
    steady_threshold: float = 0.02,
    min_samples: int = 4,
) -> TrackFieldPairCandidate | None:
    """Rank one raw range-like/velocity-like field pair.

    The method derives raw range slope between consecutive range samples and
    compares its sign and shape with the nearest raw velocity sample. Because
    scale/sign conventions are unknown, both velocity polarities are considered
    and the better relation is retained. This is discovery evidence only.
    """
    rs = _series(frames, range_field)
    vs = _series(frames, velocity_field)
    if len(rs) < 2 or not vs:
        return None

    slopes: list[float] = []
    velocities: list[float] = []
    sign_hits_direct = 0
    sign_hits_inverse = 0
    sign_trials = 0
    steady_trials = 0
    steady_hits = 0

    for (t0, r0), (t1, r1) in zip(rs, rs[1:]):
        dt = t1 - t0
        if dt <= 1e-9:
            continue
        slope = (r1 - r0) / dt
        v = _nearest(vs, (t0 + t1) * 0.5, max_pair_dt)
        if v is None:
            continue
        slopes.append(slope)
        velocities.append(v)

        if abs(slope) > 1e-12 and abs(v) > 1e-12:
            sign_trials += 1
            if slope * v > 0:
                sign_hits_direct += 1
            if slope * v < 0:
                sign_hits_inverse += 1

        if abs(slope) <= steady_threshold:
            steady_trials += 1
            if abs(v) <= max(steady_threshold, 1.0):
                steady_hits += 1

    samples = len(slopes)
    if samples < min_samples:
        return None

    sign_agreement = 1.0 if sign_trials == 0 else max(sign_hits_direct, sign_hits_inverse) / sign_trials
    corr = _pearson(slopes, velocities)
    corr_abs = abs(corr)
    steady_consistency = 1.0 if steady_trials == 0 else steady_hits / steady_trials

    # Same-bus proximity is only a weak heuristic: related FRR fields may live in
    # different messages, so cross-message pairs are still allowed and ranked.
    same_bus = range_field.bus == velocity_field.bus
    locality = 1.0 if same_bus else 0.85
    sample_factor = min(1.0, samples / 12.0)
    score = (0.50 * sign_agreement + 0.35 * corr_abs + 0.15 * steady_consistency) * locality * sample_factor

    return TrackFieldPairCandidate(
        range_field=range_field,
        velocity_field=velocity_field,
        score=score,
        samples=samples,
        derivative_sign_agreement=sign_agreement,
        correlation_abs=corr_abs,
        steady_consistency=steady_consistency,
        same_bus=same_bus,
    )


def rank_range_velocity_pairs(
    frames: list[Frame],
    range_fields: list[RawField],
    velocity_fields: list[RawField],
    *,
    max_pair_dt: float = 0.08,
    min_samples: int = 4,
) -> list[TrackFieldPairCandidate]:
    ranked: list[TrackFieldPairCandidate] = []
    for r in range_fields:
        for v in velocity_fields:
            if r == v:
                continue
            candidate = score_range_velocity_pair(
                frames,
                r,
                v,
                max_pair_dt=max_pair_dt,
                min_samples=min_samples,
            )
            if candidate is not None:
                ranked.append(candidate)
    ranked.sort(key=lambda c: (-c.score, -c.samples, c.range_field.bus, c.range_field.address, c.velocity_field.address))
    return ranked
