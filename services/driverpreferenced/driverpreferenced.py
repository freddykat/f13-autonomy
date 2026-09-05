"""Passive driver preference learning for M0 shadow mode.

Learns only from actions that are already marked legal, physically safe and
vehicle-capable. Preference learning can bias tie-breaking but cannot override
legal/safety/capability gates.
"""

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class DriverPreferenceProfile:
    overtake_bias: float = 0.0
    return_right_bias: float = 0.0
    following_time_gap_s: float = 2.0
    longitudinal_aggressiveness: float = 0.5
    sample_count: int = 0


@dataclass(frozen=True)
class Observation:
    action: str
    legal: bool
    physically_safe: bool
    vehicle_capable: bool
    following_time_gap_s: float | None = None
    longitudinal_aggressiveness: float | None = None


def _ema(old: float, new: float, alpha: float = 0.1) -> float:
    return old * (1.0 - alpha) + new * alpha


def update(profile: DriverPreferenceProfile, obs: Observation) -> DriverPreferenceProfile:
    # Never learn preferences from actions that violate hard gates.
    if not (obs.legal and obs.physically_safe and obs.vehicle_capable):
        return profile

    p = profile
    overtake = p.overtake_bias
    return_right = p.return_right_bias
    gap = p.following_time_gap_s
    aggr = p.longitudinal_aggressiveness

    if obs.action == "LEFT":
        overtake = _ema(overtake, 1.0)
    elif obs.action == "KEEP":
        overtake = _ema(overtake, 0.0)
    elif obs.action == "RIGHT":
        return_right = _ema(return_right, 1.0)

    if obs.following_time_gap_s is not None and obs.following_time_gap_s > 0:
        gap = _ema(gap, obs.following_time_gap_s)

    if obs.longitudinal_aggressiveness is not None:
        bounded = min(1.0, max(0.0, obs.longitudinal_aggressiveness))
        aggr = _ema(aggr, bounded)

    return replace(
        p,
        overtake_bias=overtake,
        return_right_bias=return_right,
        following_time_gap_s=gap,
        longitudinal_aggressiveness=aggr,
        sample_count=p.sample_count + 1,
    )


def preference_score(profile: DriverPreferenceProfile, action: str) -> float:
    if action == "LEFT":
        return profile.overtake_bias
    if action == "RIGHT":
        return profile.return_right_bias
    if action == "KEEP":
        return round(1.0 - profile.overtake_bias, 12)
    return 0.0
