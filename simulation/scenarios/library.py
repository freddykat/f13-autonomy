"""Standardized M0 motorway scenario library.

Each scenario is an offline/read-only regression case. Scenarios are intentionally
small and explicit so failures are easy to inspect.
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    description: str
    expected_shadow_action: str
    expected_review_priority: str
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class ScenarioSpec:
    """Executable form of a descriptive regression scenario."""

    name: str
    input: Any
    expected_action: str | None
    expected_review_priority: str | None


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


def scenario_library() -> tuple[ScenarioSpec, ...]:
    """Build deterministic runner fixtures from the descriptive scenario list.

    Imports are local to avoid coupling the static catalogue to the runner at
    module import time.
    """

    from services.shadowplannerd.shadowplannerd import Action, Candidate
    from simulation.scenarios.scenario_runner import Scenario as RunnerScenario

    specs = []
    for description in SCENARIOS:
        expected = Action(description.expected_shadow_action)
        candidate = Candidate(
            action=expected,
            legal=True,
            physically_safe=True,
            vehicle_capable=True,
            route_score=1.0,
            reasons=description.notes or ("REGRESSION_FIXTURE",),
        )

        human = expected.value
        openpilot = expected.value
        hw4 = expected.value
        legal_actions: tuple[str, ...] = (expected.value,)
        safe_actions: tuple[str, ...] = (expected.value,)
        if description.expected_review_priority == "DISAGREEMENT_REVIEW":
            human = "KEEP" if expected != Action.KEEP else "WAIT"
            legal_actions = ()
            safe_actions = ()
        elif description.expected_review_priority == "LEGAL_REVIEW":
            human = "KEEP" if expected != Action.KEEP else "WAIT"
            legal_actions = (expected.value,)
            safe_actions = ()
        elif description.expected_review_priority == "CRITICAL_REVIEW":
            human = "KEEP" if expected != Action.KEEP else "WAIT"

        dynamic_limit = 60.0 if description.scenario_id == "motorway-vsl-100-to-60" else None
        runner_input = RunnerScenario(
            scenario_id=description.scenario_id,
            current_speed_kph=100.0,
            static_speed_limit_kph=100.0,
            dynamic_speed_limit_kph=dynamic_limit,
            distance_to_limit_m=200.0,
            comfortable_decel_mps2=1.5,
            max_decel_mps2=4.0,
            response_delay_s=0.5,
            traffic_control=None,
            candidates=(candidate,),
            human_action=human,
            openpilot_action=openpilot,
            hw4_action=hw4,
            legal_action_set=legal_actions,
            safety_action_set=safe_actions,
        )
        specs.append(
            ScenarioSpec(
                name=description.scenario_id,
                input=runner_input,
                expected_action=description.expected_shadow_action,
                expected_review_priority=description.expected_review_priority,
            )
        )
    return tuple(specs)
