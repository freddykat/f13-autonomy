"""Traffic-control integration helpers for the read-only M0 shadow planner.

This module translates synthetic/normalized TrafficControlState into planner
constraints. It has no vehicle actuation path.
"""

from dataclasses import dataclass
from typing import Iterable

from services.shadowplannerd.shadowplannerd import Action, Candidate, ShadowDecision, choose


@dataclass(frozen=True)
class TrafficControlSummary:
    must_stop: bool = False
    current_lane_closed: bool = False
    requested_merge: Action | None = None
    speed_limit_kph: float | None = None
    stale: bool = False
    confidence: float = 1.0


def plan_with_traffic_control(
    control: TrafficControlSummary,
    *,
    left_safe: bool | None,
    right_safe: bool | None,
    left_capable: bool | None = True,
    right_capable: bool | None = True,
    keep_legal: bool | None = True,
) -> ShadowDecision:
    """Create a deterministic advisory decision from dynamic traffic controls.

    Behaviour is deliberately conservative: stale/low-confidence controls do not
    authorize manoeuvres. A confirmed red light produces STOP. A confirmed red-X
    on the current lane makes KEEP illegal and seeks a safe/capable adjacent lane.
    """

    if control.stale or control.confidence < 0.6:
        return choose([
            Candidate(Action.WAIT, True, True, True, route_score=1.0,
                      reasons=("TRAFFIC_CONTROL_UNCERTAIN",)),
        ])

    if control.must_stop:
        return choose([
            Candidate(Action.STOP, True, True, True, route_score=10.0,
                      reasons=("TRAFFIC_SIGNAL_STOP",)),
        ])

    if control.current_lane_closed:
        candidates: list[Candidate] = [
            Candidate(Action.KEEP, False, True, True, route_score=-10.0,
                      reasons=("CURRENT_LANE_CLOSED",)),
            Candidate(Action.LEFT, True, left_safe, left_capable, route_score=2.0,
                      reasons=("EXIT_CLOSED_LANE", "LEFT_OPTION")),
            Candidate(Action.RIGHT, True, right_safe, right_capable, route_score=1.9,
                      reasons=("EXIT_CLOSED_LANE", "RIGHT_OPTION")),
            Candidate(Action.SLOW, True, True, True, route_score=1.0,
                      reasons=("CLOSED_LANE_NO_IMMEDIATE_GAP",)),
        ]
        return choose(candidates)

    if control.requested_merge in (Action.LEFT, Action.RIGHT):
        target = control.requested_merge
        safe = left_safe if target == Action.LEFT else right_safe
        capable = left_capable if target == Action.LEFT else right_capable
        return choose([
            Candidate(Action.KEEP, keep_legal, True, True, route_score=0.2),
            Candidate(target, True, safe, capable, route_score=1.0,
                      reasons=("MATRIX_MERGE_DIRECTION",)),
        ])

    return choose([
        Candidate(Action.KEEP, keep_legal, True, True, route_score=1.0,
                  reasons=("NO_DYNAMIC_TRAFFIC_CONSTRAINT",)),
    ])
