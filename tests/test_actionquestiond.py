from services.actionquestiond.actionquestiond import IntentContext, QuestionPolicy, decide


def ctx(**kwargs):
    base = dict(
        legal_known=True, safety_known=True, capability_known=True,
        valid_options=("KEEP", "LEFT"), decision_margin=0.5,
        time_to_decision_s=20.0, driver_available=True,
    )
    base.update(kwargs)
    return IntentContext(**base)


def test_never_asks_driver_to_resolve_safety_unknown():
    q = decide(ctx(safety_known=False, decision_margin=0.01))
    assert q.policy == QuestionPolicy.WAIT_CONSERVATIVELY
    assert q.prompt is None


def test_never_asks_driver_to_resolve_legality_unknown():
    q = decide(ctx(legal_known=False, route_requires_choice=True))
    assert q.policy == QuestionPolicy.WAIT_CONSERVATIVELY


def test_asks_when_two_safe_legal_options_are_close():
    q = decide(ctx(decision_margin=0.05))
    assert q.policy == QuestionPolicy.ASK_DRIVER
    assert q.options == ("KEEP", "LEFT")


def test_route_choice_can_trigger_question():
    q = decide(ctx(route_requires_choice=True, decision_margin=0.5))
    assert q.policy == QuestionPolicy.ASK_DRIVER


def test_short_horizon_does_not_distract_with_question():
    q = decide(ctx(decision_margin=0.01, time_to_decision_s=3.0))
    assert q.policy == QuestionPolicy.WAIT_CONSERVATIVELY
    assert q.prompt is None


def test_single_valid_option_needs_no_question():
    q = decide(ctx(valid_options=("KEEP",)))
    assert q.policy == QuestionPolicy.NO_QUESTION
    assert q.default_action == "KEEP"


def test_no_valid_option_recommends_takeover():
    q = decide(ctx(valid_options=()))
    assert q.policy == QuestionPolicy.TAKEOVER_RECOMMENDED
