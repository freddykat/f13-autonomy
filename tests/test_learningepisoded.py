from services.learningepisoded.learningepisoded import (
    AdvisorDecisions, LearningEpisode, Outcome, to_jsonl, validate_for_learning,
)


def episode(**kwargs):
    base = dict(
        episode_id="ep-001",
        timestamp_ns=123,
        jurisdiction="NL",
        road_type="motorway",
        world_state={"objects": 3},
        bmw_vehicle_state={"speed_mps": 27.8},
        traffic_rule_context={"speed_limit_kph": 100},
        traffic_control_state={"vsl_kph": 80},
        bmw_dynamic_capability={"comfortableMaxAccel": 1.4},
        odd_state={"mode": "SHADOW_ONLY"},
        advisor_decisions=AdvisorDecisions(human="KEEP", openpilot="KEEP", shadow="KEEP", hw4_benchmark="KEEP"),
        shadow_reason_codes=("VALID_HIGHEST_PRIORITY_OPTION",),
        disagreement_priority="CONSENSUS",
        outcome=Outcome(observed_action="KEEP", min_time_gap_s=2.1),
    )
    base.update(kwargs)
    return LearningEpisode(**base)


def test_valid_episode_can_enter_learning_pool():
    ok, reasons = validate_for_learning(episode())
    assert ok
    assert reasons == ()


def test_missing_outcome_blocks_learning():
    ok, reasons = validate_for_learning(episode(outcome=None))
    assert not ok
    assert "OUTCOME_MISSING" in reasons


def test_legal_violation_blocks_learning():
    ok, reasons = validate_for_learning(episode(outcome=Outcome(observed_action="LEFT", legal_violation_detected=True)))
    assert not ok
    assert "LEGAL_VIOLATION" in reasons


def test_intervention_required_blocks_preference_learning():
    ok, reasons = validate_for_learning(episode(outcome=Outcome(observed_action="KEEP", intervention_required=True)))
    assert not ok
    assert "INTERVENTION_REQUIRED" in reasons


def test_unknown_jurisdiction_blocks_learning():
    ok, reasons = validate_for_learning(episode(jurisdiction="UNKNOWN"))
    assert not ok
    assert "JURISDICTION_UNKNOWN" in reasons


def test_serialization_is_deterministic():
    a = to_jsonl(episode())
    b = to_jsonl(episode())
    assert a == b
    assert '"episode_id":"ep-001"' in a
    assert "\n" not in a
