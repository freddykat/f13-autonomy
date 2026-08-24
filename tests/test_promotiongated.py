from services.promotiongated.promotiongated import (
    PromotionDecision,
    PromotionEvidence,
    evaluate,
)


def evidence(**kwargs):
    base = dict(
        exam_total=100,
        exam_passed=100,
        replay_total=200,
        replay_improvements=5,
        replay_regressions=0,
        critical_regressions=0,
        unresolved_cases=0,
        jurisdiction_coverage=4,
        required_jurisdictions=4,
        scenario_coverage_ratio=1.0,
    )
    base.update(kwargs)
    return PromotionEvidence(**base)


def test_all_gates_pass_only_marks_next_stage_eligible():
    r = evaluate(evidence())
    assert r.decision == PromotionDecision.ELIGIBLE_FOR_NEXT_VALIDATION_STAGE


def test_any_replay_regression_blocks_promotion():
    r = evaluate(evidence(replay_regressions=1))
    assert r.decision == PromotionDecision.BLOCK
    assert "REPLAY_REGRESSION_PRESENT" in r.reasons


def test_critical_regression_blocks_promotion():
    r = evaluate(evidence(critical_regressions=1))
    assert r.decision == PromotionDecision.BLOCK


def test_low_exam_score_keeps_shadow_only():
    r = evaluate(evidence(exam_passed=95))
    assert r.decision == PromotionDecision.SHADOW_ONLY
    assert "EXAM_PASS_RATE_TOO_LOW" in r.reasons


def test_insufficient_replay_data_keeps_shadow_only():
    r = evaluate(evidence(replay_total=20))
    assert r.decision == PromotionDecision.SHADOW_ONLY


def test_incomplete_jurisdiction_coverage_keeps_shadow_only():
    r = evaluate(evidence(jurisdiction_coverage=3))
    assert r.decision == PromotionDecision.SHADOW_ONLY


def test_unresolved_cases_prevent_promotion():
    r = evaluate(evidence(unresolved_cases=2))
    assert r.decision == PromotionDecision.SHADOW_ONLY
