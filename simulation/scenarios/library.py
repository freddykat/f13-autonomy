"""Standardized M0 motorway scenario library.

Each scenario is an offline/read-only regression case. Scenarios are intentionally
small and explicit so failures are easy to inspect.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    description: str
    expected_shadow_action: str
    expected_review_priority: str
    notes: tuple[str, ...] = ()


SCENARIOS = (
    Scenario(
        "motorway-clear-road",
        "Clear motorway, no hazards, no route pressure.",
        "KEEP",
        "CONSENSUS",
        ("baseline",),
    ),
    Scenario(
        "motorway-slow-lead-safe-left",
        "Slower lead vehicle, left lane gap safe and manoeuvre legal.",
        "LEFT",
        "CONSENSUS",
        ("overtake", "safe-gap"),
    ),
    Scenario(
        "motorway-fast-rear-left",
        "Slower lead vehicle but fast rear-left vehicle closes the gap.",
        "KEEP",
        "DISAGREEMENT_REVIEW",
        ("rear-closing-speed",),
    ),
    Scenario(
        "motorway-cut-in",
        "Adjacent vehicle cuts into ego lane at short range.",
        "SLOW",
        "CRITICAL_REVIEW",
        ("cut-in", "longitudinal-margin"),
    ),
    Scenario(
        "motorway-red-x-current-lane",
        "Current lane receives red-X matrix indication; adjacent lane is safe.",
        "LEFT",
        "CONSENSUS",
        ("matrix", "lane-closure"),
    ),
    Scenario(
        "motorway-vsl-100-to-60",
        "Dynamic speed limit changes from 100 km/h to 60 km/h ahead.",
        "SLOW",
        "CONSENSUS",
        ("vsl", "anticipatory-deceleration"),
    ),
    Scenario(
        "motorway-lane-ending",
        "Ego lane ends ahead and left merge is legal and physically safe.",
        "LEFT",
        "CONSENSUS",
        ("lane-ending", "merge"),
    ),
    Scenario(
        "motorway-merge-insufficient-bmw-capability",
        "Merge gap exists geometrically but predicted BMW response is insufficient.",
        "WAIT",
        "DISAGREEMENT_REVIEW",
        ("bmw-capability", "response-delay"),
    ),
    Scenario(
        "motorway-exit-approach",
        "Navigation exit approaches; route requires preparing for the right lane.",
        "RIGHT",
        "CONSENSUS",
        ("route-intent", "exit"),
    ),
    Scenario(
        "motorway-stopped-obstacle",
        "Stopped obstacle occupies ego path.",
        "STOP",
        "CRITICAL_REVIEW",
        ("occupancy", "stopped-object"),
    ),
    Scenario(
        "motorway-radar-dropout",
        "Radar becomes stale while camera remains available.",
        "WAIT",
        "DISAGREEMENT_REVIEW",
        ("sensor-dropout", "radar"),
    ),
    Scenario(
        "motorway-camera-dropout",
        "Primary camera state becomes stale while radar remains available.",
        "WAIT",
        "DISAGREEMENT_REVIEW",
        ("sensor-dropout", "camera"),
    ),
    Scenario(
        "motorway-traffic-control-unknown",
        "Dynamic traffic-control perception is stale or confidence is insufficient.",
        "WAIT",
        "DISAGREEMENT_REVIEW",
        ("traffic-control", "unknown"),
    ),
)


BY_ID = {scenario.scenario_id: scenario for scenario in SCENARIOS}


def get_scenario(scenario_id: str) -> Scenario:
    return BY_ID[scenario_id]
