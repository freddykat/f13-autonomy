"""Offline replay validator for recorded learning episodes.

Re-runs a supplied planner function against recorded episode context and compares
old vs new advisory decisions. No vehicle actuation path.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Iterable, Mapping


class ReplayChange(str, Enum):
    UNCHANGED = "UNCHANGED"
    IMPROVEMENT = "IMPROVEMENT"
    REGRESSION = "REGRESSION"
    CHANGED_NEUTRAL = "CHANGED_NEUTRAL"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class ReplayEpisode:
    episode_id: str
    old_action: str | None
    legal_action_set: tuple[str, ...]
    safety_action_set: tuple[str, ...]
    preferred_reference_action: str | None
    context: Mapping[str, Any]


@dataclass(frozen=True)
class ReplayResult:
    episode_id: str
    old_action: str | None
    new_action: str | None
    change: ReplayChange
    reason: str


def _is_valid(action: str | None, legal: set[str], safe: set[str]) -> bool | None:
    if action is None:
        return None
    if legal and action not in legal:
        return False
    if safe and action not in safe:
        return False
    return True


def compare(episode: ReplayEpisode, new_action: str | None) -> ReplayResult:
    if new_action is None:
        return ReplayResult(episode.episode_id, episode.old_action, None, ReplayChange.UNRESOLVED, "NEW_DECISION_MISSING")
    if episode.old_action == new_action:
        return ReplayResult(episode.episode_id, episode.old_action, new_action, ReplayChange.UNCHANGED, "SAME_ACTION")

    legal = set(episode.legal_action_set)
    safe = set(episode.safety_action_set)
    old_valid = _is_valid(episode.old_action, legal, safe)
    new_valid = _is_valid(new_action, legal, safe)

    if old_valid is False and new_valid is True:
        return ReplayResult(episode.episode_id, episode.old_action, new_action, ReplayChange.IMPROVEMENT, "MOVED_INTO_VALID_ACTION_SET")
    if old_valid is True and new_valid is False:
        return ReplayResult(episode.episode_id, episode.old_action, new_action, ReplayChange.REGRESSION, "MOVED_OUTSIDE_VALID_ACTION_SET")

    ref = episode.preferred_reference_action
    if ref is not None:
        if new_action == ref and episode.old_action != ref and new_valid is not False:
            return ReplayResult(episode.episode_id, episode.old_action, new_action, ReplayChange.IMPROVEMENT, "MATCHES_VALIDATED_REFERENCE")
        if episode.old_action == ref and new_action != ref:
            return ReplayResult(episode.episode_id, episode.old_action, new_action, ReplayChange.REGRESSION, "DEVIATES_FROM_VALIDATED_REFERENCE")

    return ReplayResult(episode.episode_id, episode.old_action, new_action, ReplayChange.CHANGED_NEUTRAL, "ACTION_CHANGED_WITHOUT_PROVEN_QUALITY_DELTA")


def validate(episodes: Iterable[ReplayEpisode], planner: Callable[[Mapping[str, Any]], str | None]) -> tuple[ReplayResult, ...]:
    return tuple(compare(ep, planner(ep.context)) for ep in episodes)


def summary(results: Iterable[ReplayResult]) -> dict[str, int]:
    counts = {change.value: 0 for change in ReplayChange}
    for result in results:
        counts[result.change.value] += 1
    return counts
