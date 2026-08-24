from services.disagreementd.disagreementd import DecisionSample, analyse, to_jsonl


def sample(**kwargs):
    base = dict(timestamp_ns=1, scenario_id="motorway-001")
    base.update(kwargs)
    return DecisionSample(**base)


def test_consensus():
    e = analyse(sample(human="KEEP", openpilot="KEEP", shadow="KEEP", hw4_benchmark="KEEP"))
    assert not e.disagreement
    assert e.priority == "CONSENSUS"


def test_plain_disagreement_is_saved_for_review():
    e = analyse(sample(human="LEFT", openpilot="KEEP", shadow="LEFT", hw4_benchmark="LEFT"))
    assert e.disagreement
    assert e.priority == "DISAGREEMENT_REVIEW"
    assert e.unique_actions == ("KEEP", "LEFT")


def test_majority_does_not_override_legality():
    e = analyse(sample(
        human="LEFT", openpilot="LEFT", shadow="KEEP", hw4_benchmark="LEFT",
        legal_action_set=("KEEP", "RIGHT"),
    ))
    assert e.priority == "LEGAL_REVIEW"
    assert set(e.legal_conflict_sources) == {"human", "openpilot", "hw4_benchmark"}


def test_safety_conflict_has_highest_review_priority():
    e = analyse(sample(
        human="LEFT", openpilot="LEFT", shadow="WAIT", hw4_benchmark="LEFT",
        legal_action_set=("LEFT", "WAIT"), safety_action_set=("WAIT",),
    ))
    assert e.priority == "CRITICAL_REVIEW"
    assert set(e.safety_conflict_sources) == {"human", "openpilot", "hw4_benchmark"}


def test_missing_sources_are_allowed():
    e = analyse(sample(shadow="KEEP", openpilot="KEEP"))
    assert e.available_sources == 2
    assert e.priority == "CONSENSUS"


def test_jsonl_is_deterministic():
    e = analyse(sample(shadow="KEEP"))
    line = to_jsonl(e)
    assert '"scenario_id":"motorway-001"' in line
    assert "\n" not in line
