#!/usr/bin/env python3
"""Offline FRR/ACC relational discovery for passive BMW traces.

This module operates only on already-ranked continuous candidates. It never
transmits, assigns engineering units, writes DBCs, or promotes decoders.
"""

from __future__ import annotations

from dataclasses import dataclass
from collections import defaultdict
from typing import Iterable

from tools.bmw_continuous_signal_correlation import ContinuousCandidate


@dataclass(frozen=True)
class FRRRelationSpec:
    closing_event: str = "LEAD_CLOSING"
    opening_event: str = "LEAD_OPENING"
    steady_event: str | None = "LEAD_STEADY"
    loss_event: str | None = "LEAD_LOSS"


@dataclass(frozen=True)
class FRRRelationalCandidate:
    bus: str
    address: int
    start_byte: int
    width: int
    signed: bool
    endian: str
    score: float
    coverage: float
    opposite_direction_score: float
    steady_score: float
    loss_transition_score: float
    closing_mean_delta: float | None
    opening_mean_delta: float | None
    steady_mean_delta: float | None
    loss_mean_delta: float | None
    kind: str = "frr_relational_integer"


def _feature_key(c: ContinuousCandidate) -> tuple[str, int, int, int, bool, str]:
    return (c.bus, c.address, c.start_byte, c.width, c.signed, c.endian)


def _best_by_event(candidates: Iterable[ContinuousCandidate]) -> dict[tuple, dict[str, ContinuousCandidate]]:
    grouped: dict[tuple, dict[str, ContinuousCandidate]] = defaultdict(dict)
    for c in candidates:
        key = _feature_key(c)
        prev = grouped[key].get(c.event)
        if prev is None or (c.score, c.observations) > (prev.score, prev.observations):
            grouped[key][c.event] = c
    return grouped


def rank_frr_relational_candidates(
    candidates: Iterable[ContinuousCandidate],
    *,
    spec: FRRRelationSpec | None = None,
    min_event_score: float = 0.0,
) -> list[FRRRelationalCandidate]:
    """Rank raw fields that behave coherently across lead-relative events.

    For a distance-like raw field we want closing/opening to move in opposite
    directions. We do not assume which sign corresponds to increasing physical
    range. A steady event is rewarded for a smaller raw delta than dynamic
    events. A loss event is treated only as an observable transition signal;
    it is not assumed to encode a particular invalid value.
    """
    spec = spec or FRRRelationSpec()
    grouped = _best_by_event(candidates)
    out: list[FRRRelationalCandidate] = []

    required = [spec.closing_event, spec.opening_event]
    optional = [e for e in (spec.steady_event, spec.loss_event) if e]

    for key, events in grouped.items():
        if any(e not in events for e in required):
            continue
        if any(events[e].score < min_event_score for e in required):
            continue

        closing = events[spec.closing_event]
        opening = events[spec.opening_event]
        c_delta = closing.mean_delta
        o_delta = opening.mean_delta

        opposite = 1.0 if c_delta * o_delta < 0 else 0.0

        dynamic_mag = max(abs(c_delta), abs(o_delta), 1e-12)
        steady_delta = None
        steady_score = 0.5  # neutral if not observed
        if spec.steady_event and spec.steady_event in events:
            steady_delta = events[spec.steady_event].mean_delta
            steady_score = max(0.0, min(1.0, 1.0 - abs(steady_delta) / dynamic_mag))

        loss_delta = None
        loss_score = 0.5  # neutral if not observed
        if spec.loss_event and spec.loss_event in events:
            loss_delta = events[spec.loss_event].mean_delta
            # We only reward a distinct transition; no specific sentinel/value
            # is assumed because invalid/stale semantics are vehicle-dependent.
            loss_score = min(1.0, abs(loss_delta) / dynamic_mag)

        present = sum(e in events for e in required + optional)
        coverage = present / max(1, len(required) + len(optional))
        event_quality = min(1.0, (closing.score + opening.score) / 2.0)

        score = (
            0.45 * opposite
            + 0.20 * steady_score
            + 0.15 * loss_score
            + 0.10 * coverage
            + 0.10 * event_quality
        )

        bus, address, start_byte, width, signed, endian = key
        out.append(FRRRelationalCandidate(
            bus=bus,
            address=address,
            start_byte=start_byte,
            width=width,
            signed=signed,
            endian=endian,
            score=score,
            coverage=coverage,
            opposite_direction_score=opposite,
            steady_score=steady_score,
            loss_transition_score=loss_score,
            closing_mean_delta=c_delta,
            opening_mean_delta=o_delta,
            steady_mean_delta=steady_delta,
            loss_mean_delta=loss_delta,
        ))

    out.sort(key=lambda c: (-c.score, -c.coverage, c.bus, c.address, c.start_byte, c.width, c.signed, c.endian))
    return out
