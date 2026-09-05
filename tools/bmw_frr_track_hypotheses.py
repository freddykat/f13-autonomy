#!/usr/bin/env python3
"""Build passive FRR track hypotheses from raw candidate evidence.

This module deliberately stops before decoder promotion or openpilot RadarData.
It combines already-discovered candidate fields into ranked hypotheses while
keeping all raw identities and uncertainty explicit.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class RawFieldRef:
    bus: str
    address: int
    start_byte: int
    width: int
    signed: bool
    endian: str


@dataclass(frozen=True)
class TrackFieldCandidate:
    field: RawFieldRef
    role_hint: str
    score: float
    observations: int


@dataclass(frozen=True)
class FRRTrackHypothesis:
    range_field: RawFieldRef
    velocity_field: RawFieldRef
    validity_field: RawFieldRef | None
    lateral_field: RawFieldRef | None
    track_id_field: RawFieldRef | None
    score: float
    evidence_coverage: float
    same_bus_score: float
    same_address_score: float
    role_count: int
    mode: str = "OFFLINE_READ_ONLY_DISCOVERY"
    auto_promote: bool = False
    actuation: str = "NONE"


def _compatibility(a: RawFieldRef, b: RawFieldRef) -> tuple[float, float]:
    return (1.0 if a.bus == b.bus else 0.25, 1.0 if a.address == b.address else 0.5)


def _best_optional(
    candidates: Iterable[TrackFieldCandidate],
    role: str,
    anchor: RawFieldRef,
) -> TrackFieldCandidate | None:
    relevant = [c for c in candidates if c.role_hint == role]
    if not relevant:
        return None
    return max(
        relevant,
        key=lambda c: (
            c.score * (1.0 if c.field.bus == anchor.bus else 0.6) * (1.0 if c.field.address == anchor.address else 0.8),
            c.observations,
        ),
    )


def build_track_hypotheses(
    range_candidates: Iterable[TrackFieldCandidate],
    velocity_candidates: Iterable[TrackFieldCandidate],
    optional_candidates: Iterable[TrackFieldCandidate] = (),
    *,
    min_score: float = 0.0,
) -> list[FRRTrackHypothesis]:
    """Rank combinations of raw FRR field candidates without assigning units.

    `role_hint` is discovery metadata only. Optional roles currently recognized:
    validity, lateral, track_id. No result becomes a decoder entry automatically.
    """
    ranges = [c for c in range_candidates if c.role_hint == "range"]
    velocities = [c for c in velocity_candidates if c.role_hint == "velocity"]
    optionals = list(optional_candidates)
    out: list[FRRTrackHypothesis] = []

    for r in ranges:
        for v in velocities:
            same_bus, same_addr = _compatibility(r.field, v.field)
            validity = _best_optional(optionals, "validity", r.field)
            lateral = _best_optional(optionals, "lateral", r.field)
            track_id = _best_optional(optionals, "track_id", r.field)
            selected = [x for x in (validity, lateral, track_id) if x is not None]

            base = 0.45 * r.score + 0.45 * v.score
            topology = 0.06 * same_bus + 0.04 * same_addr
            optional_bonus = sum(min(1.0, max(0.0, c.score)) for c in selected) * (0.05 / 3.0)
            score = min(1.0, base + topology + optional_bonus)
            if score < min_score:
                continue

            role_count = 2 + len(selected)
            evidence_coverage = role_count / 5.0
            out.append(FRRTrackHypothesis(
                range_field=r.field,
                velocity_field=v.field,
                validity_field=validity.field if validity else None,
                lateral_field=lateral.field if lateral else None,
                track_id_field=track_id.field if track_id else None,
                score=score,
                evidence_coverage=evidence_coverage,
                same_bus_score=same_bus,
                same_address_score=same_addr,
                role_count=role_count,
            ))

    out.sort(key=lambda h: (-h.score, -h.evidence_coverage, -h.role_count, h.range_field.bus, h.range_field.address))
    return out
