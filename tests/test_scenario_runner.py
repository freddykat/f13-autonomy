from simulation.scenarios.scenario_runner import Scenario, result_json, run_scenario
from services.shadowplannerd.shadowplannerd import Action, Candidate
from services.trafficcontrold.trafficcontrold import TrafficControlInput


def cand(action, legal=True, safe=True, capable=True, route=0.0, pref=0.0, reasons=()):
    return Candidate(action, legal, safe, capable, route, pref, reasons)


def test_red_x_safe_left_escape_and_vsl():
    s = Scenario(
        scenario_id="red-x-left-escape",
        current_speed_kph=100.0,
        static_speed_limit_kph=100.0,
        dynamic_speed_limit_kph=80.0,
        distance_to_limit_m=250.0,
        comfortable_decel_mps2=1.5,
        max_decel_mps2=3.0,
        response_delay_s=0.5,
        traffic_control=TrafficControlInput(kind="RED_X", state="ACTIVE", lane_id="current", confidence=0.99, stale=False),
        candidates=(
            cand(Action.KEEP, safe=False),
            cand(Action.LEFT, route=1.0, reasons=("RED_X_EXIT", "LEFT_GAP_SAFE")),
        ),
        human_action="LEFT",
        openpilot_action="LEFT",
        hw4_action="LEFT",
        legal_action_set=("LEFT", "RIGHT"),
        safety_action_set=("LEFT",),
    )
    r = run_scenario(s)
    assert r.shadow.action == Action.LEFT
    assert r.longitudinal.target_speed_kph == 80.0
    assert r.disagreement.priority == "CONSENSUS"


def test_unsafe_left_creates_disagreement_review():
    s = Scenario(
        scenario_id="unsafe-left",
        current_speed_kph=100.0,
        static_speed_limit_kph=100.0,
        dynamic_speed_limit_kph=None,
        distance_to_limit_m=None,
        comfortable_decel_mps2=1.5,
        max_decel_mps2=3.0,
        response_delay_s=0.8,
        traffic_control=None,
        candidates=(
            cand(Action.KEEP, route=0.1),
            cand(Action.LEFT, safe=False, route=1.0),
        ),
        human_action="LEFT",
        openpilot_action="LEFT",
        hw4_action="LEFT",
        legal_action_set=("KEEP", "LEFT"),
        safety_action_set=("KEEP",),
    )
    r = run_scenario(s)
    assert r.shadow.action == Action.KEEP
    assert r.disagreement.priority == "CRITICAL_REVIEW"


def test_result_is_serializable():
    s = Scenario(
        scenario_id="serialize",
        current_speed_kph=90.0,
        static_speed_limit_kph=100.0,
        dynamic_speed_limit_kph=None,
        distance_to_limit_m=None,
        comfortable_decel_mps2=1.5,
        max_decel_mps2=3.0,
        response_delay_s=0.5,
        traffic_control=None,
        candidates=(cand(Action.KEEP),),
    )
    line = result_json(run_scenario(s))
    assert '"scenario_id":"serialize"' in line
    assert "\n" not in line
