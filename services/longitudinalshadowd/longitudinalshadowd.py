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


@dataclass(frozen=True)
class LongitudinalPlan:
    """Compatibility envelope used by the composed M0 scenario runner.

    The core supervisor works in SI units.  This envelope exposes the normalized
    target in km/h to the older scenario fixtures without creating a second
    decision algorithm.
    """

    target_speed_kph: float | None
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
    *args: float | BMWLongitudinalCapability | SpeedConstraint,
    current_speed_mps: float | None = None,
    distance_to_constraint_m: float | None = None,
    capability: BMWLongitudinalCapability | None = None,
) -> LongitudinalShadowDecision:
    """Evaluate a speed constraint using either positional or keyword core inputs.

    Some early fixtures supplied the constraints positionally after keyword core
    inputs, while others supplied every input positionally. Supporting both keeps
    one underlying algorithm and makes the public test contract unambiguous.
    """

    if current_speed_mps is None:
        if len(args) < 3:
            raise TypeError("evaluate requires speed, distance and capability")
        current_speed_mps = float(args[0])
        distance_to_constraint_m = float(args[1])
        candidate_capability = args[2]
        if not isinstance(candidate_capability, BMWLongitudinalCapability):
            raise TypeError("third positional argument must be BMWLongitudinalCapability")
        capability = candidate_capability
        constraints = args[3:]
    else:
        if distance_to_constraint_m is None or capability is None:
            raise TypeError("keyword evaluation requires distance_to_constraint_m and capability")
        constraints = args
    if not all(isinstance(item, SpeedConstraint) for item in constraints):
        raise TypeError("all remaining arguments must be SpeedConstraint values")

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


def plan_speed(
    *,
    current_speed_kph: float,
    static_speed_limit_kph: float | None,
    dynamic_speed_limit_kph: float | None,
    distance_to_limit_m: float | None,
    comfortable_decel_mps2: float,
    max_decel_mps2: float,
    response_delay_s: float,
) -> LongitudinalPlan:
    """Adapt legacy scenario inputs to the SI-unit shadow evaluator."""

    constraints = []
    if static_speed_limit_kph is not None:
        constraints.append(SpeedConstraint(static_speed_limit_kph / 3.6, "static", 1.0))
    if dynamic_speed_limit_kph is not None:
        constraints.append(SpeedConstraint(dynamic_speed_limit_kph / 3.6, "dynamic", 1.0))
    capability = BMWLongitudinalCapability(
        comfortable_decel_mps2=comfortable_decel_mps2,
        max_decel_mps2=max_decel_mps2,
        response_delay_s=response_delay_s,
        confidence=1.0,
    )
    decision = evaluate(
        current_speed_kph / 3.6,
        float("inf") if distance_to_limit_m is None else distance_to_limit_m,
        capability,
        *constraints,
    )
    return LongitudinalPlan(
        target_speed_kph=None if decision.target_speed_mps is None else decision.target_speed_mps * 3.6,
        required_decel_mps2=decision.required_decel_mps2,
        feasible_comfortably=decision.feasible_comfortably,
        feasible_max=decision.feasible_max,
        start_reducing_now=decision.start_reducing_now,
        reason_codes=decision.reason_codes,
        confidence=decision.confidence,
    )


def stopping_distance_for_speed_change(current_speed_mps: float, target_speed_mps: float, decel_mps2: float, delay_s: float = 0.0) -> float:
    if current_speed_mps <= target_speed_mps:
        return 0.0
    if decel_mps2 <= 0:
        return float("inf")
    reaction = current_speed_mps * max(0.0, delay_s)
    braking = (current_speed_mps**2 - target_speed_mps**2) / (2.0 * decel_mps2)
    return reaction + braking
