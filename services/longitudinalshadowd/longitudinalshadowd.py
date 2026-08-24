"""Read-only longitudinal shadow supervisor for M0.

Combines static/dynamic speed constraints with a simple BMW capability model.
No vehicle actuation path exists in this module.
"""

from dataclasses import dataclass
from math import sqrt


@dataclass(frozen=True)
class SpeedConstraint:
    speed_mps: float | None
    source: str
    confidence: float
    stale: bool = False


@dataclass(frozen=True)
class BMWLongitudinalCapability:
    comfortable_decel_mps2: float
    max_decel_mps2: float
    response_delay_s: float
    confidence: float


@dataclass(frozen=True)
class LongitudinalShadowDecision:
    target_speed_mps: float | None
    required_decel_mps2: float | None
    feasible_comfortably: bool | None
    feasible_max: bool | None
    start_reducing_now: bool
    reason_codes: tuple[str, ...]
    confidence: float


def effective_speed_limit(*constraints: SpeedConstraint) -> tuple[float | None, tuple[str, ...], float]:
    valid = [c for c in constraints if c.speed_mps is not None and not c.stale and c.confidence >= 0.7]
    if not valid:
        return None, ("SPEED_LIMIT_UNKNOWN",), 0.0
    winner = min(valid, key=lambda c: c.speed_mps)
    return winner.speed_mps, (f"LIMIT_FROM_{winner.source.upper()}",), winner.confidence


def required_constant_decel(current_speed_mps: float, target_speed_mps: float, distance_m: float) -> float:
    if distance_m <= 0:
        return float("inf") if current_speed_mps > target_speed_mps else 0.0
    if current_speed_mps <= target_speed_mps:
        return 0.0
    return (current_speed_mps**2 - target_speed_mps**2) / (2.0 * distance_m)


def evaluate(
    current_speed_mps: float,
    distance_to_constraint_m: float,
    capability: BMWLongitudinalCapability,
    *constraints: SpeedConstraint,
) -> LongitudinalShadowDecision:
    target, reasons, limit_conf = effective_speed_limit(*constraints)
    if target is None:
        return LongitudinalShadowDecision(None, None, None, None, False, reasons, 0.0)

    # Account conservatively for powertrain/chassis response delay by consuming distance
    # at current speed before assuming useful deceleration begins.
    effective_distance = max(0.0, distance_to_constraint_m - current_speed_mps * capability.response_delay_s)
    req = required_constant_decel(current_speed_mps, target, effective_distance)

    if req == float("inf"):
        comfortable = False
        max_ok = False
    else:
        comfortable = req <= capability.comfortable_decel_mps2
        max_ok = req <= capability.max_decel_mps2

    reason_codes = list(reasons)
    if current_speed_mps > target:
        reason_codes.append("REDUCTION_REQUIRED")
    if not max_ok:
        reason_codes.append("INSUFFICIENT_DECEL_DISTANCE")
    elif not comfortable:
        reason_codes.append("COMFORT_MARGIN_EXCEEDED")
    else:
        reason_codes.append("COMFORTABLY_FEASIBLE")

    start_now = current_speed_mps > target and (req > 0 or effective_distance <= 0)
    confidence = min(limit_conf, capability.confidence)
    return LongitudinalShadowDecision(target, req, comfortable, max_ok, start_now, tuple(reason_codes), confidence)


def stopping_distance_for_speed_change(current_speed_mps: float, target_speed_mps: float, decel_mps2: float, delay_s: float = 0.0) -> float:
    if current_speed_mps <= target_speed_mps:
        return 0.0
    if decel_mps2 <= 0:
        return float("inf")
    reaction = current_speed_mps * max(0.0, delay_s)
    braking = (current_speed_mps**2 - target_speed_mps**2) / (2.0 * decel_mps2)
    return reaction + braking
