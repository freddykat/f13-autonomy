from simulation.scenarios.library import BY_ID, SCENARIOS, get_scenario


def test_scenario_ids_are_unique():
    ids = [s.scenario_id for s in SCENARIOS]
    assert len(ids) == len(set(ids))


def test_core_motorway_exam_cases_exist():
    required = {
        "motorway-clear-road",
        "motorway-slow-lead-safe-left",
        "motorway-fast-rear-left",
        "motorway-cut-in",
        "motorway-red-x-current-lane",
        "motorway-vsl-100-to-60",
        "motorway-lane-ending",
        "motorway-merge-insufficient-bmw-capability",
        "motorway-exit-approach",
        "motorway-stopped-obstacle",
        "motorway-radar-dropout",
        "motorway-camera-dropout",
        "motorway-traffic-control-unknown",
    }
    assert required.issubset(BY_ID)


def test_expected_actions_are_supported():
    allowed = {"KEEP", "LEFT", "RIGHT", "WAIT", "SLOW", "STOP"}
    assert all(s.expected_shadow_action in allowed for s in SCENARIOS)


def test_expected_review_priorities_are_supported():
    allowed = {"CONSENSUS", "DISAGREEMENT_REVIEW", "LEGAL_REVIEW", "CRITICAL_REVIEW"}
    assert all(s.expected_review_priority in allowed for s in SCENARIOS)


def test_lookup_returns_exact_scenario():
    s = get_scenario("motorway-stopped-obstacle")
    assert s.expected_shadow_action == "STOP"
    assert "stopped-object" in s.notes
