"""Synthetic/read-only traffic-control supervisor for M0 development.

Converts recognized traffic-control observations into deterministic advisory constraints.
No vehicle actuation path is present.
"""

from dataclasses import dataclass
from enum import Enum


class SignalKind(str, Enum):
    TRAFFIC_LIGHT = "TRAFFIC_LIGHT"
    VARIABLE_SPEED = "VARIABLE_SPEED"
    LANE_CONTROL = "LANE_CONTROL"
    WARNING = "WARNING"


class LightState(str, Enum):
    RED = "RED"
    AMBER = "AMBER"
    GREEN = "GREEN"
    FLASHING = "FLASHING"
    OFF = "OFF"
    UNKNOWN = "UNKNOWN"


class LaneControlState(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    MERGE_LEFT = "MERGE_LEFT"
    MERGE_RIGHT = "MERGE_RIGHT"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class Observation:
    timestamp_ns: int
    kind: SignalKind
    confidence: float
    lane_id: str | None = None
    light_state: LightState | None = None
    lane_control: LaneControlState | None = None
    speed_limit_kph: int | None = None
    stale: bool = False


@dataclass(frozen=True)
class TrafficControlConstraint:
    lane_id: str | None
    must_stop: bool = False
    lane_closed: bool = False
    merge_direction: str | None = None
    speed_limit_kph: int | None = None
    uncertain: bool = False
    reason: str = "NONE"


def evaluate(obs: Observation, min_confidence: float = 0.80) -> TrafficControlConstraint:
    if obs.stale or obs.confidence < min_confidence:
        return TrafficControlConstraint(obs.lane_id, uncertain=True, reason="STALE_OR_LOW_CONFIDENCE")

    if obs.kind == SignalKind.TRAFFIC_LIGHT:
        if obs.light_state == LightState.RED:
            return TrafficControlConstraint(obs.lane_id, must_stop=True, reason="RED_LIGHT")
        if obs.light_state in (LightState.UNKNOWN, LightState.OFF, None):
            return TrafficControlConstraint(obs.lane_id, uncertain=True, reason="LIGHT_STATE_UNKNOWN")
        return TrafficControlConstraint(obs.lane_id, reason=f"LIGHT_{obs.light_state.value}")

    if obs.kind == SignalKind.LANE_CONTROL:
        if obs.lane_control == LaneControlState.CLOSED:
            return TrafficControlConstraint(obs.lane_id, lane_closed=True, reason="RED_X_LANE_CLOSED")
        if obs.lane_control == LaneControlState.MERGE_LEFT:
            return TrafficControlConstraint(obs.lane_id, merge_direction="LEFT", reason="MERGE_LEFT")
        if obs.lane_control == LaneControlState.MERGE_RIGHT:
            return TrafficControlConstraint(obs.lane_id, merge_direction="RIGHT", reason="MERGE_RIGHT")
        if obs.lane_control in (LaneControlState.UNKNOWN, None):
            return TrafficControlConstraint(obs.lane_id, uncertain=True, reason="LANE_CONTROL_UNKNOWN")
        return TrafficControlConstraint(obs.lane_id, reason="LANE_OPEN")

    if obs.kind == SignalKind.VARIABLE_SPEED:
        if obs.speed_limit_kph is None:
            return TrafficControlConstraint(obs.lane_id, uncertain=True, reason="VSL_UNKNOWN")
        return TrafficControlConstraint(obs.lane_id, speed_limit_kph=obs.speed_limit_kph, reason="VARIABLE_SPEED_LIMIT")

    return TrafficControlConstraint(obs.lane_id, reason="NO_DIRECT_CONSTRAINT")
