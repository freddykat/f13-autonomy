from services.replayvalidatord.replayvalidatord import (
    ReplayChange, ReplayEpisode, compare, summary, validate,
)


def ep(**kwargs):
    base = dict(
        episode_id="ep-1",
        old_action="KEEP",
        legal_action_set=("KEEP", "LEFT"),
        safety_action_set=("KEEP", "LEFT"),
        preferred_reference_action=None,
        context={"planner_action": "KEEP"},
    )
    base.update(kwargs)
    return ReplayEpisode(**base)


def test_unchanged_action():
    r = compare(ep(), "KEEP")
    assert r.change == ReplayChange.UNCHANGED


def test_illegal_old_to_valid_new_is_improvement():
    r = compare(ep(old_action="RIGHT", legal_action_set=("KEEP", "LEFT")), "KEEP")
    assert r.change == ReplayChange.IMPROVEMENT


def test_valid_old_to_unsafe_new_is_regression():
    r = compare(ep(safety_action_set=("KEEP",)), "LEFT")
    assert r.change == ReplayChange.REGRESSION


def test_matching_validated_reference_is_improvement():
    r = compare(ep(old_action="KEEP", preferred_reference_action="LEFT"), "LEFT")
    assert r.change == ReplayChange.IMPROVEMENT


def test_leaving_validated_reference_is_regression():
    r = compare(ep(old_action="LEFT", preferred_reference_action="LEFT"), "KEEP")
    assert r.change == ReplayChange.REGRESSION


def test_neutral_change_when_quality_not_proven():
    r = compare(ep(), "LEFT")
    assert r.change == ReplayChange.CHANGED_NEUTRAL


def test_validate_runs_supplied_planner():
    episodes = (ep(), ep(episode_id="ep-2", context={"planner_action": "LEFT"}))
    results = validate(episodes, lambda ctx: ctx["planner_action"])
    assert len(results) == 2
    assert results[0].new_action == "KEEP"
    assert results[1].new_action == "LEFT"


def test_summary_counts_changes():
    results = (
        compare(ep(), "KEEP"),
        compare(ep(episode_id="ep-2"), "LEFT"),
    )
    s = summary(results)
    assert s["UNCHANGED"] == 1
    assert s["CHANGED_NEUTRAL"] == 1
