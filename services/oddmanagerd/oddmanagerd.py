"""Operational Design Domain manager for M0/M1 shadow validation.

Read-only policy layer. It classifies which autonomy mode would be allowed by the
current context; it has no actuation path.
"""

from dataclasses import dataclass
from enum import Enum


class ODDMode(str, Enum):
    MANUAL_ONLY = "MANUAL_ONLY"
    SHADOW_ONLY = "SHADOW_ONLY"
    PARTIAL_AUTOPILOT = "PARTIAL_AUTOPILOT"
    HIGHWAY_SUPERVISED = "HIGHWAY_SUPERVISED"


@dataclass(frozen=True)
class ODDInput:
    road_type: str | None
    route_active: bool
    sensors_ok: bool
    driver_monitoring_ok: bool
    visibility_ok: bool | None
    severe_weather: bool
    traffic_control_confident: bool
    jurisdiction_known: bool
    highway_validated: bool


@dataclass(frozen=True)
class ODDDecision:
    mode: ODDMode
    reasons: tuple[str, ...]


def classify(x: ODDInput) -> ODDDecision:
    reasons: list[str] = []

    if not x.sensors_ok:
        return ODDDecision(ODDMode.MANUAL_ONLY, ("SENSOR_HEALTH_INSUFFICIENT",))
    if not x.driver_monitoring_ok:
        return ODDDecision(ODDMode.MANUAL_ONLY, ("DRIVER_MONITORING_UNAVAILABLE",))
    if x.severe_weather:
        return ODDDecision(ODDMode.SHADOW_ONLY, ("SEVERE_WEATHER",))
    if x.visibility_ok is not True:
        return ODDDecision(ODDMode.SHADOW_ONLY, ("VISIBILITY_NOT_CONFIRMED",))
    if not x.jurisdiction_known:
        return ODDDecision(ODDMode.SHADOW_ONLY, ("JURISDICTION_UNKNOWN",))

    road = (x.road_type or "").upper()
    is_highway = road in {"MOTORWAY", "HIGHWAY", "AUTOBAN", "AUTOSTRADA"}

    if is_highway and x.highway_validated and x.traffic_control_confident:
        if x.route_active:
            return ODDDecision(ODDMode.HIGHWAY_SUPERVISED, ("VALIDATED_HIGHWAY_ODD", "ROUTE_ACTIVE"))
        return ODDDecision(ODDMode.PARTIAL_AUTOPILOT, ("VALIDATED_HIGHWAY_ODD", "NO_ROUTE"))

    if is_highway and not x.traffic_control_confident:
        reasons.append("TRAFFIC_CONTROL_UNCERTAIN")
    if is_highway and not x.highway_validated:
        reasons.append("HIGHWAY_NOT_VALIDATED")
    if not is_highway:
        reasons.append("ROAD_TYPE_OUTSIDE_HIGHWAY_ODD")

    return ODDDecision(ODDMode.PARTIAL_AUTOPILOT, tuple(reasons or ("PARTIAL_ONLY",)))
