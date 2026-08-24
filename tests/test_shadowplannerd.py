from services.shadowplannerd.shadowplannerd import Action, Candidate, choose


def c(action, legal=True, safe=True, capable=True, route=0.0, pref=0.0, reasons=()):
    return Candidate(action, legal, safe, capable, route, pref, reasons)


def test_safe_overtake_left():
    d = choose([
        c(Action.KEEP, route=0.1),
        c(Action.LEFT, route=0.5, pref=0.2, reasons=("SLOW_LEAD", "LEFT_GAP_SAFE")),
    ])
    assert d.action == Action.LEFT


def test_fast_rear_left_rejects_lane_change():
    d = choose([
        c(Action.KEEP, route=0.1),
        c(Action.LEFT, safe=False, route=0.8),
    ])
    assert d.action == Action.KEEP
    assert (Action.LEFT, "UNSAFE") in d.rejected


def test_insufficient_bmw_accel_rejects_merge():
    d = choose([
        c(Action.WAIT, route=0.1, reasons=("WAIT_FOR_GAP",)),
        c(Action.LEFT, capable=False, route=0.9),
    ])
    assert d.action == Action.WAIT
    assert (Action.LEFT, "BMW_CAPABILITY_INSUFFICIENT") in d.rejected


def test_illegal_action_never_wins():
    d = choose([
        c(Action.KEEP, route=0.0),
        c(Action.LEFT, legal=False, route=100.0),
    ])
    assert d.action == Action.KEEP


def test_unknown_legality_fails_closed_for_optional_manoeuvre():
    d = choose([
        c(Action.KEEP, route=0.0),
        c(Action.RIGHT, legal=None, route=1.0),
    ])
    assert d.action == Action.KEEP
    assert (Action.RIGHT, "LEGALITY_UNKNOWN") in d.rejected


def test_route_beats_preference_after_gates():
    d = choose([
        c(Action.LEFT, route=0.9, pref=0.0),
        c(Action.KEEP, route=0.2, pref=1.0),
    ])
    assert d.action == Action.LEFT


def test_no_candidates_waits():
    d = choose([])
    assert d.action == Action.WAIT
    assert d.confidence == 0.0
