"""Structured offline recorder for learning/replay episodes.

This module stores context and advisory decisions for later analysis. It has no
vehicle actuation authority.
"""

from dataclasses import asdict, dataclass
from typing import Any, Mapping
import json


@dataclass(frozen=True)
class AdvisorDecisions:
    human: str | None = None
    openpilot: str | None = None
    shadow: str | None = None
    hw4_benchmark: str | None = None


@dataclass(frozen=True)
class Outcome:
    observed_action: str | None
    min_time_gap_s: float | None = None
    max_lateral_accel_mps2: float | None = None
    max_longitudinal_accel_mps2: float | None = None
    dsc_intervention: bool = False
    intervention_required: bool = False
    legal_violation_detected: bool = False
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class LearningEpisode:
    episode_id: str
    timestamp_ns: int
    jurisdiction: str
    road_type: str
    world_state: Mapping[str, Any]
    bmw_vehicle_state: Mapping[str, Any]
    traffic_rule_context: Mapping[str, Any]
    traffic_control_state: Mapping[str, Any]
    bmw_dynamic_capability: Mapping[str, Any]
    odd_state: Mapping[str, Any]
    advisor_decisions: AdvisorDecisions
    shadow_reason_codes: tuple[str, ...]
    disagreement_priority: str
    outcome: Outcome | None = None
    schema_version: int = 1


def validate_for_learning(ep: LearningEpisode) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if ep.outcome is None:
        reasons.append("OUTCOME_MISSING")
    else:
        if ep.outcome.legal_violation_detected:
            reasons.append("LEGAL_VIOLATION")
        if ep.outcome.intervention_required:
            reasons.append("INTERVENTION_REQUIRED")
    if not ep.jurisdiction or ep.jurisdiction == "UNKNOWN":
        reasons.append("JURISDICTION_UNKNOWN")
    return (len(reasons) == 0, tuple(reasons))


def to_json(ep: LearningEpisode) -> str:
    return json.dumps(asdict(ep), sort_keys=True, separators=(",", ":"))


def to_jsonl(ep: LearningEpisode) -> str:
    return to_json(ep)
