from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class SignalState(str, Enum):
    VALID = "valid"
    STALE = "stale"
    UNKNOWN = "unknown"


@dataclass(slots=True)
class PlannedMotion:
    timestamp_s: float
    speed_mps: float
    accel_mps2: float
    curvature_1pm: float
    yaw_rate_rps: Optional[float] = None


@dataclass(slots=True)
class BMWChassisState:
    timestamp_s: float
    speed_mps: float
    yaw_rate_rps: Optional[float]
    lateral_accel_mps2: Optional[float]
    longitudinal_accel_mps2: Optional[float]
    front_steer_deg: Optional[float]
    rear_steer_deg: Optional[float]
    rear_steer_state: SignalState
    dsc_intervening: bool = False
    icm_state: SignalState = SignalState.VALID
    eps_state: SignalState = SignalState.VALID


@dataclass(slots=True)
class DynamicCapabilityState:
    timestamp_s: float
    max_accel_mps2: float
    comfortable_max_accel_mps2: float
    min_accel_mps2: float
    response_delay_s: float
    max_jerk_mps3: float
    downshift_likely: bool
    shift_in_progress: bool
    traction_limited: bool
    thermal_limited: bool
    confidence: float


@dataclass(slots=True)
class MotionValidationState:
    timestamp_s: float
    speed_error_mps: Optional[float]
    accel_error_mps2: Optional[float]
    curvature_error_1pm: Optional[float]
    yaw_rate_error_rps: Optional[float]
    rear_steer_known: bool
    oem_stability_intervention: bool
    confidence: float
    status: str
