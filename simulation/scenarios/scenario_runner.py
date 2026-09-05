"""Offline M0 scenario runner for Prototype 001.

This module composes existing read-only/shadow components into a single deterministic
scenario result. It has no vehicle actuation path.
"""

from dataclasses import asdict, dataclass
import json

from services.disagreementd.disagreementd import DecisionSample, DisagreementEvent, analyse
from services.longitudinalshadowd.longitudinalshadowd import LongitudinalPlan, plan_speed
from services.shadowplannerd.shadowplannerd import Action, Candidate, ShadowDecision, choose
from services.trafficcontrold.trafficcontrold import TrafficControlInput, TrafficControlDecision, evaluate


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    current_speed_kph: float
    static_speed_limit_kph: float | None
    dynamic_speed_limit_kph: float | None
    distance_to_limit_m: float | None
    comfortable_decel_mps2: float
    max_decel_mps2: float
    response_delay_s: float
    traffic_control: TrafficControlInput | None
    candidates: tuple[Candidate, ...]
    human_action: str | None = None
    openpilot_action: str | None = None
    hw4_action: str | None = None
    legal_action_set: tuple[str, ...] = ()
    safety_action_set: tuple[str, ...] = ()


@dataclass(frozen=True)
class ScenarioResult:
    scenario_id: str
    traffic: TrafficControlDecision | None
    longitudinal: LongitudinalPlan
    shadow: ShadowDecision
    disagreement: DisagreementEvent

    @property
    def shadow_decision(self) -> ShadowDecision:
        """Backward-compatible name used by the M0 exam runner."""

        return self.shadow


def run_scenario(s: Scenario) -> ScenarioResult:
    traffic = evaluate(s.traffic_control) if s.traffic_control is not None else None

    longitudinal = plan_speed(
        current_speed_kph=s.current_speed_kph,
        static_speed_limit_kph=s.static_speed_limit_kph,
        dynamic_speed_limit_kph=s.dynamic_speed_limit_kph,
        distance_to_limit_m=s.distance_to_limit_m,
        comfortable_decel_mps2=s.comfortable_decel_mps2,
        max_decel_mps2=s.max_decel_mps2,
        response_delay_s=s.response_delay_s,
    )

    shadow = choose(s.candidates)

    disagreement = analyse(
        DecisionSample(
            timestamp_ns=0,
            scenario_id=s.scenario_id,
            human=s.human_action,
            openpilot=s.openpilot_action,
            shadow=shadow.action.value,
            hw4_benchmark=s.hw4_action,
            legal_action_set=s.legal_action_set,
            safety_action_set=s.safety_action_set,
        )
    )

    return ScenarioResult(
        scenario_id=s.scenario_id,
        traffic=traffic,
        longitudinal=longitudinal,
        shadow=shadow,
        disagreement=disagreement,
    )


def result_json(result: ScenarioResult) -> str:
    return json.dumps(asdict(result), sort_keys=True, separators=(",", ":"), default=str)
