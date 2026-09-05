#!/usr/bin/env python3
"""Cross-session evidence aggregation for passive BMW function hypotheses.

Consumes outputs from bmw_function_identifier.py and ranks whether the exact
same raw feature behaves like the same function across independent sessions.
No decoder promotion, engineering scaling, transport translation, diagnostic
writes, transmit paths, or vehicle-control authority are created here.
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SessionHypothesis:
    session_id: str
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
    score: float
    direction_score: float
    baseline_score: float
    transition_strength: float
    coverage_score: float
    raw_polarity: str
    bus: str | None = None
    address: int | None = None
    channel: str | None = None
    slot_id: int | None = None
    cycle: int | None = None
    base_cycle: int | None = None
    cycle_repetition: int | None = None
    frame_id: int | None = None


@dataclass(frozen=True)
class BMWFunctionEvidence:
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
    bus: str | None
    address: int | None
    channel: str | None
    slot_id: int | None
    cycle: int | None
    base_cycle: int | None
    cycle_repetition: int | None
    frame_id: int | None
    sessions_observed: int
    sessions_total: int
    session_coverage: float
    mean_score: float
    minimum_score: float
    score_stability: float
    polarity_consistency: float
    mean_direction_score: float
    mean_baseline_score: float
    evidence_score: float
    confidence: str
    corroboration_state: str
    status: str = "UNVALIDATED_CROSS_SESSION_EVIDENCE"


def _optional_int(item: dict[str, Any], name: str) -> int | None:
    value = item.get(name)
    return None if value is None else int(value)


def _optional_bool(item: dict[str, Any], name: str) -> bool | None:
    value = item.get(name)
    return None if value is None else bool(value)


def _parse_hypothesis(session_id: str, item: dict[str, Any]) -> SessionHypothesis:
    return SessionHypothesis(
        session_id=session_id,
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
        score=float(item["score"]),
        direction_score=float(item.get("direction_score", 0.0)),
        baseline_score=float(item.get("baseline_score", 1.0)),
        transition_strength=float(item.get("transition_strength", 0.0)),
        coverage_score=float(item.get("coverage_score", 0.0)),
        raw_polarity=str(item.get("raw_polarity", "unknown")),
        bus=None if item.get("bus") is None else str(item["bus"]),
        address=_optional_int(item, "address"),
        channel=None if item.get("channel") is None else str(item["channel"]),
        slot_id=_optional_int(item, "slot_id"),
        cycle=_optional_int(item, "cycle"),
        base_cycle=_optional_int(item, "base_cycle"),
        cycle_repetition=_optional_int(item, "cycle_repetition"),
        frame_id=_optional_int(item, "frame_id"),
    )


def load_session(path: Path) -> tuple[str, list[SessionHypothesis]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    session_id = str(payload.get("session_id", path.stem))
    items = payload.get("hypotheses")
    if not isinstance(items, list):
        raise ValueError(f"{path}: missing hypotheses list")
    return session_id, [_parse_hypothesis(session_id, item) for item in items]


def _identity_key(item: SessionHypothesis) -> tuple[Any, ...]:
    """Exact raw-feature identity across independent capture sessions."""
    return (
        item.function_family,
        item.function_kind,
        item.transport,
        item.source_key,
        item.feature_kind,
        item.start_byte,
        item.width,
        item.bit,
        item.signed,
        item.endian,
    )


def _mean(values: list[float]) -> float:
    return statistics.fmean(values) if values else 0.0


def _score_stability(scores: list[float]) -> float:
    """1.0 for stable scores, decreasing with cross-session spread."""
    if not scores:
        return 0.0
    if len(scores) == 1:
        return 0.5
    spread = max(scores) - min(scores)
    return max(0.0, 1.0 - spread)


def _polarity_consistency(items: list[SessionHypothesis]) -> float:
    polarities = [item.raw_polarity for item in items if item.raw_polarity != "unknown"]
    if not polarities:
        return 0.5
    counts: dict[str, int] = defaultdict(int)
    for polarity in polarities:
        counts[polarity] += 1
    return max(counts.values()) / len(polarities)


def _confidence(
    *,
    sessions_observed: int,
    session_coverage: float,
    evidence_score: float,
    polarity_consistency: float,
) -> str:
    """Evidence confidence only; never means vehicle-validated decoder."""
    if (
        sessions_observed >= 3
        and session_coverage >= 0.75
        and evidence_score >= 0.85
        and polarity_consistency >= 0.9
    ):
        return "HIGH"
    if (
        sessions_observed >= 2
        and session_coverage >= 0.5
        and evidence_score >= 0.65
        and polarity_consistency >= 0.75
    ):
        return "MEDIUM"
    return "LOW"


def aggregate_function_evidence(
    sessions: list[tuple[str, list[SessionHypothesis]]],
    *,
    minimum_hypothesis_score: float = 0.0,
) -> list[BMWFunctionEvidence]:
    """Aggregate exact raw-feature hypotheses across independent sessions."""
    if not sessions:
        return []

    total_sessions = len({session_id for session_id, _ in sessions})
    grouped: dict[tuple[Any, ...], dict[str, SessionHypothesis]] = defaultdict(dict)

    for session_id, hypotheses in sessions:
        for item in hypotheses:
            if item.score < minimum_hypothesis_score:
                continue
            key = _identity_key(item)
            previous = grouped[key].get(session_id)
            if previous is None or item.score > previous.score:
                grouped[key][session_id] = item

    evidence: list[BMWFunctionEvidence] = []
    for session_map in grouped.values():
        items = list(session_map.values())
        representative = max(items, key=lambda item: item.score)
        scores = [item.score for item in items]
        direction_scores = [item.direction_score for item in items]
        baseline_scores = [item.baseline_score for item in items]

        sessions_observed = len(items)
        session_coverage = sessions_observed / float(total_sessions)
        mean_score = _mean(scores)
        minimum_score = min(scores)
        stability = _score_stability(scores)
        polarity = _polarity_consistency(items)
        mean_direction = _mean(direction_scores)
        mean_baseline = _mean(baseline_scores)

        # Repeatability and agreement are primary. A single excellent session
        # cannot outrank a slightly weaker candidate repeated across sessions.
        evidence_score = (
            0.35 * session_coverage
            + 0.25 * mean_score
            + 0.15 * minimum_score
            + 0.10 * stability
            + 0.10 * polarity
            + 0.05 * mean_direction
        )

        confidence = _confidence(
            sessions_observed=sessions_observed,
            session_coverage=session_coverage,
            evidence_score=evidence_score,
            polarity_consistency=polarity,
        )

        evidence.append(BMWFunctionEvidence(
            function_family=representative.function_family,
            function_kind=representative.function_kind,
            transport=representative.transport,
            source_key=representative.source_key,
            feature_kind=representative.feature_kind,
            start_byte=representative.start_byte,
            width=representative.width,
            bit=representative.bit,
            signed=representative.signed,
            endian=representative.endian,
            bus=representative.bus,
            address=representative.address,
            channel=representative.channel,
            slot_id=representative.slot_id,
            cycle=representative.cycle,
            base_cycle=representative.base_cycle,
            cycle_repetition=representative.cycle_repetition,
            frame_id=representative.frame_id,
            sessions_observed=sessions_observed,
            sessions_total=total_sessions,
            session_coverage=session_coverage,
            mean_score=mean_score,
            minimum_score=minimum_score,
            score_stability=stability,
            polarity_consistency=polarity,
            mean_direction_score=mean_direction,
            mean_baseline_score=mean_baseline,
            evidence_score=evidence_score,
            confidence=confidence,
            corroboration_state="NOT_YET_CORROBORATED",
        ))

    evidence.sort(key=lambda item: (
        -item.evidence_score,
        -item.sessions_observed,
        item.function_family,
        item.transport,
        item.source_key,
        item.start_byte,
        -1 if item.bit is None else item.bit,
        -1 if item.width is None else item.width,
    ))
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Aggregate passive BMW function hypotheses across sessions"
    )
    parser.add_argument("sessions", type=Path, nargs="+")
    parser.add_argument("--minimum-hypothesis-score", type=float, default=0.0)
    parser.add_argument("--top", type=int, default=200)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    loaded = [load_session(path) for path in args.sessions]
    evidence = aggregate_function_evidence(
        loaded,
        minimum_hypothesis_score=args.minimum_hypothesis_score,
    )
    payload = {
        "mode": "OFFLINE_READ_ONLY_EVIDENCE_AGGREGATION",
        "status": "UNVALIDATED_CROSS_SESSION_EVIDENCE",
        "sessions": [session_id for session_id, _ in loaded],
        "auto_promote": False,
        "vehicle_validated": False,
        "decoder_generation": False,
        "diagnostic_writes": False,
        "transmit": False,
        "actuation_authority": "NONE",
        "evidence": [asdict(item) for item in evidence[: args.top]],
    }
    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
