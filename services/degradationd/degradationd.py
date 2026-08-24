"""Read-only M0 sensor-health and degradation manager.

This module evaluates autonomy capability from sensor/subsystem health. It produces
advisory mode recommendations only and has no vehicle actuation path.
"""

from dataclasses import dataclass
from enum import Enum


class Health(str, Enum):
    OK = "OK"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


class CapabilityMode(str, Enum):
    FULL_SHADOW = "FULL_SHADOW"
    PARTIAL_SHADOW = "PARTIAL_SHADOW"
    MINIMAL_SHADOW = "MINIMAL_SHADOW"
    TAKEOVER_RECOMMENDED = "TAKEOVER_RECOMMENDED"


@dataclass(frozen=True)
class SensorHealthState:
    cameras: Health
    radar: Health
    bmw_buses: Health
    imu: Health
    gnss: Health
    traffic_control: Health
    driver_monitoring: Health


@dataclass(frozen=True)
class DegradationDecision:
    mode: CapabilityMode
    reason_codes: tuple[str, ...]
    confidence: float


def evaluate(h: SensorHealthState) -> DegradationDecision:
    reasons: list[str] = []

    # Core ego-motion / vehicle-state observability is mandatory even in shadow mode.
    if h.bmw_buses in {Health.FAILED, Health.UNKNOWN}:
        return DegradationDecision(CapabilityMode.TAKEOVER_RECOMMENDED, ("BMW_STATE_UNAVAILABLE",), 0.99)
    if h.imu in {Health.FAILED, Health.UNKNOWN}:
        return DegradationDecision(CapabilityMode.TAKEOVER_RECOMMENDED, ("IMU_UNAVAILABLE",), 0.95)

    # Primary scene perception loss is severe.
    if h.cameras == Health.FAILED and h.radar == Health.FAILED:
        return DegradationDecision(CapabilityMode.TAKEOVER_RECOMMENDED, ("PRIMARY_PERCEPTION_LOST",), 0.99)

    mode = CapabilityMode.FULL_SHADOW

    if h.cameras in {Health.DEGRADED, Health.UNKNOWN}:
        mode = CapabilityMode.PARTIAL_SHADOW
        reasons.append("CAMERA_DEGRADED")
    elif h.cameras == Health.FAILED:
        mode = CapabilityMode.MINIMAL_SHADOW
        reasons.append("CAMERA_FAILED")

    if h.radar in {Health.DEGRADED, Health.UNKNOWN}:
        if mode == CapabilityMode.FULL_SHADOW:
            mode = CapabilityMode.PARTIAL_SHADOW
        reasons.append("RADAR_DEGRADED")
    elif h.radar == Health.FAILED:
        if mode == CapabilityMode.FULL_SHADOW:
            mode = CapabilityMode.PARTIAL_SHADOW
        reasons.append("RADAR_FAILED")

    if h.traffic_control in {Health.DEGRADED, Health.UNKNOWN}:
        if mode == CapabilityMode.FULL_SHADOW:
            mode = CapabilityMode.PARTIAL_SHADOW
        reasons.append("TRAFFIC_CONTROL_UNCERTAIN")
    elif h.traffic_control == Health.FAILED:
        mode = CapabilityMode.MINIMAL_SHADOW
        reasons.append("TRAFFIC_CONTROL_FAILED")

    if h.gnss in {Health.DEGRADED, Health.UNKNOWN, Health.FAILED}:
        if mode == CapabilityMode.FULL_SHADOW:
            mode = CapabilityMode.PARTIAL_SHADOW
        reasons.append("GNSS_DEGRADED")

    if h.driver_monitoring in {Health.DEGRADED, Health.UNKNOWN, Health.FAILED}:
        if mode == CapabilityMode.FULL_SHADOW:
            mode = CapabilityMode.PARTIAL_SHADOW
        reasons.append("DRIVER_MONITORING_DEGRADED")

    confidence = {
        CapabilityMode.FULL_SHADOW: 0.95,
        CapabilityMode.PARTIAL_SHADOW: 0.80,
        CapabilityMode.MINIMAL_SHADOW: 0.60,
        CapabilityMode.TAKEOVER_RECOMMENDED: 0.99,
    }[mode]

    return DegradationDecision(mode, tuple(reasons) or ("ALL_REQUIRED_SOURCES_HEALTHY",), confidence)
