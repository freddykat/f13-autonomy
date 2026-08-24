"""Offline gate for staged controlled-vehicle validation.

This module does not send vehicle commands. It only determines whether evidence
from one controlled-test stage is sufficient to advance to the next stage.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ControlledVehicleEvidence:
    hil_eligible: bool
    promotion_gate_passed: bool
    critical_anomalies: int = 0
    required_signals_stale: int = 0
    unexplained_motion_disagreements: int = 0
    driver_override_verified: bool = False
    emergency_stop_verified: bool = False
    watchdog_verified: bool = False
    test_stage_passed: bool = False


@dataclass(frozen=True)
class ControlledVehicleGateResult:
    eligible_for_next_stage: bool
    blockers: tuple[str, ...]


def evaluate(e: ControlledVehicleEvidence, *, next_stage_requires_authority: bool = False) -> ControlledVehicleGateResult:
    blockers: list[str] = []

    if not e.hil_eligible:
        blockers.append("HIL_NOT_ELIGIBLE")
    if not e.promotion_gate_passed:
        blockers.append("PROMOTION_GATE_NOT_PASSED")
    if e.critical_anomalies:
        blockers.append("CRITICAL_ANOMALY_PRESENT")
    if e.required_signals_stale:
        blockers.append("REQUIRED_SIGNAL_STALENESS")
    if e.unexplained_motion_disagreements:
        blockers.append("UNEXPLAINED_MOTION_DISAGREEMENT")
    if not e.test_stage_passed:
        blockers.append("CURRENT_STAGE_NOT_PASSED")

    if next_stage_requires_authority:
        if not e.driver_override_verified:
            blockers.append("DRIVER_OVERRIDE_NOT_VERIFIED")
        if not e.emergency_stop_verified:
            blockers.append("EMERGENCY_STOP_NOT_VERIFIED")
        if not e.watchdog_verified:
            blockers.append("WATCHDOG_NOT_VERIFIED")

    return ControlledVehicleGateResult(not blockers, tuple(blockers))
