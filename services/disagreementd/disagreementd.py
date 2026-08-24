"""Offline disagreement mining for Prototype 001.

Records advisory decisions from independent sources. It does not control a vehicle
and does not treat majority vote as ground truth.
"""

from dataclasses import asdict, dataclass
from typing import Mapping
import json


@dataclass(frozen=True)
class DecisionSample:
    timestamp_ns: int
    scenario_id: str
    human: str | None = None
    openpilot: str | None = None
    shadow: str | None = None
    hw4_benchmark: str | None = None
    legal_action_set: tuple[str, ...] = ()
    safety_action_set: tuple[str, ...] = ()


@dataclass(frozen=True)
class DisagreementEvent:
    sample: DecisionSample
    available_sources: int
    unique_actions: tuple[str, ...]
    disagreement: bool
    legal_conflict_sources: tuple[str, ...]
    safety_conflict_sources: tuple[str, ...]
    priority: str


def analyse(sample: DecisionSample) -> DisagreementEvent:
    decisions: Mapping[str, str | None] = {
        "human": sample.human,
        "openpilot": sample.openpilot,
        "shadow": sample.shadow,
        "hw4_benchmark": sample.hw4_benchmark,
    }
    present = {name: action for name, action in decisions.items() if action is not None}
    unique = tuple(sorted(set(present.values())))
    legal = set(sample.legal_action_set)
    safe = set(sample.safety_action_set)
    legal_conflicts = tuple(sorted(name for name, action in present.items() if legal and action not in legal))
    safety_conflicts = tuple(sorted(name for name, action in present.items() if safe and action not in safe))

    if safety_conflicts:
        priority = "CRITICAL_REVIEW"
    elif legal_conflicts:
        priority = "LEGAL_REVIEW"
    elif len(unique) > 1:
        priority = "DISAGREEMENT_REVIEW"
    else:
        priority = "CONSENSUS"

    return DisagreementEvent(
        sample=sample,
        available_sources=len(present),
        unique_actions=unique,
        disagreement=len(unique) > 1,
        legal_conflict_sources=legal_conflicts,
        safety_conflict_sources=safety_conflicts,
        priority=priority,
    )


def to_jsonl(event: DisagreementEvent) -> str:
    return json.dumps(asdict(event), sort_keys=True, separators=(",", ":"))
