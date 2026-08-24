"""Deterministic M0 shadow planner.

Read-only/offline by design. This module produces advisory decisions only and has
no vehicle actuation path.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable


class Action(str, Enum):
    KEEP = "KEEP"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    WAIT = "WAIT"
    SLOW = "SLOW"
    STOP = "STOP"


@dataclass(frozen=True)
class Candidate:
    action: Action
    legal: bool | None
    physically_safe: bool | None
    vehicle_capable: bool | None
    route_score: float = 0.0
    preference_score: float = 0.0
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class ShadowDecision:
    action: Action
    confidence: float
    reason_codes: tuple[str, ...]
    rejected: tuple[tuple[Action, str], ...] = field(default_factory=tuple)


def _reject_reason(c: Candidate) -> str | None:
    # Optional manoeuvres fail closed on unknown legality/safety/capability.
    if c.legal is False:
        return "ILLEGAL"
    if c.legal is None:
        return "LEGALITY_UNKNOWN"
    if c.physically_safe is False:
        return "UNSAFE"
    if c.physically_safe is None:
        return "SAFETY_UNKNOWN"
    if c.vehicle_capable is False:
        return "BMW_CAPABILITY_INSUFFICIENT"
    if c.vehicle_capable is None:
        return "BMW_CAPABILITY_UNKNOWN"
    return None


def choose(candidates: Iterable[Candidate]) -> ShadowDecision:
    candidates = tuple(candidates)
    if not candidates:
        return ShadowDecision(Action.WAIT, 0.0, ("NO_CANDIDATES",))

    accepted: list[Candidate] = []
    rejected: list[tuple[Action, str]] = []
    for c in candidates:
        reason = _reject_reason(c)
        if reason is None:
            accepted.append(c)
        else:
            rejected.append((c.action, reason))

    if not accepted:
        # STOP wins if explicitly supplied as a valid emergency fallback; otherwise WAIT.
        return ShadowDecision(Action.WAIT, 0.25, ("NO_VALID_OPTION",), tuple(rejected))

    # Legality/safety/capability have already gated candidates. Route intent outranks
    # behavioural preference. Stable enum value gives deterministic tie-breaking.
    accepted.sort(key=lambda c: (c.route_score, c.preference_score, c.action.value), reverse=True)
    winner = accepted[0]
    confidence = 0.9 if len(accepted) == 1 else 0.75
    reasons = winner.reasons or ("VALID_HIGHEST_PRIORITY_OPTION",)
    return ShadowDecision(winner.action, confidence, reasons, tuple(rejected))
