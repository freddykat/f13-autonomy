from __future__ import annotations

from dataclasses import replace

from simulation.m0_types import BMWChassisState, SignalState


def straight(timestamp_s: float = 0.0, speed_mps: float = 27.8) -> BMWChassisState:
    return BMWChassisState(
        timestamp_s=timestamp_s,
        speed_mps=speed_mps,
        yaw_rate_rps=0.0,
        lateral_accel_mps2=0.0,
        longitudinal_accel_mps2=0.0,
        front_steer_deg=0.0,
        rear_steer_deg=0.0,
        rear_steer_state=SignalState.VALID,
    )


def motorway_curve(timestamp_s: float = 0.0, speed_mps: float = 27.8) -> BMWChassisState:
    return BMWChassisState(
        timestamp_s=timestamp_s,
        speed_mps=speed_mps,
        yaw_rate_rps=0.055,
        lateral_accel_mps2=1.53,
        longitudinal_accel_mps2=0.0,
        front_steer_deg=1.2,
        rear_steer_deg=0.18,
        rear_steer_state=SignalState.VALID,
    )


def low_speed_rear_steer(timestamp_s: float = 0.0, speed_mps: float = 2.0) -> BMWChassisState:
    return BMWChassisState(
        timestamp_s=timestamp_s,
        speed_mps=speed_mps,
        yaw_rate_rps=0.12,
        lateral_accel_mps2=0.24,
        longitudinal_accel_mps2=0.0,
        front_steer_deg=12.0,
        rear_steer_deg=-2.0,
        rear_steer_state=SignalState.VALID,
    )


def with_stale_rear_steer(state: BMWChassisState) -> BMWChassisState:
    return replace(state, rear_steer_deg=None, rear_steer_state=SignalState.STALE)


def with_dsc_intervention(state: BMWChassisState) -> BMWChassisState:
    return replace(state, dsc_intervening=True)
