from __future__ import annotations

from simulation.m0_types import (
    BMWChassisState,
    MotionValidationState,
    PlannedMotion,
    SignalState,
)


def _curvature_from_yaw(speed_mps: float, yaw_rate_rps: float | None) -> float | None:
    if yaw_rate_rps is None or abs(speed_mps) < 0.5:
        return None
    return yaw_rate_rps / speed_mps


def validate_motion(planned: PlannedMotion, observed: BMWChassisState) -> MotionValidationState:
    curvature = _curvature_from_yaw(observed.speed_mps, observed.yaw_rate_rps)

    speed_error = observed.speed_mps - planned.speed_mps
    accel_error = None
    if observed.longitudinal_accel_mps2 is not None:
        accel_error = observed.longitudinal_accel_mps2 - planned.accel_mps2

    curvature_error = None if curvature is None else curvature - planned.curvature_1pm

    yaw_error = None
    if planned.yaw_rate_rps is not None and observed.yaw_rate_rps is not None:
        yaw_error = observed.yaw_rate_rps - planned.yaw_rate_rps

    rear_known = (
        observed.rear_steer_state == SignalState.VALID
        and observed.rear_steer_deg is not None
    )

    confidence = 1.0
    if observed.icm_state != SignalState.VALID:
        confidence -= 0.30
    if observed.eps_state != SignalState.VALID:
        confidence -= 0.25
    if not rear_known:
        confidence -= 0.15
    if observed.yaw_rate_rps is None:
        confidence -= 0.20
    confidence = max(0.0, min(1.0, confidence))

    if observed.dsc_intervening:
        status = "OEM_STABILITY_INTERVENTION"
    elif confidence < 0.5:
        status = "LOW_CONFIDENCE"
    else:
        status = "OBSERVING"

    return MotionValidationState(
        timestamp_s=max(planned.timestamp_s, observed.timestamp_s),
        speed_error_mps=speed_error,
        accel_error_mps2=accel_error,
        curvature_error_1pm=curvature_error,
        yaw_rate_error_rps=yaw_error,
        rear_steer_known=rear_known,
        oem_stability_intervention=observed.dsc_intervening,
        confidence=confidence,
        status=status,
    )
