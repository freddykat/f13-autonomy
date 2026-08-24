from simulation.scenarios.exam_runner import ExamScorecard, render_markdown, run_exam


def test_exam_returns_scorecard():
    score = run_exam()
    assert isinstance(score, ExamScorecard)
    assert score.total >= 10
    assert score.passed + score.failed == score.total
    assert 0.0 <= score.pass_rate <= 1.0


def test_each_case_has_expected_and_actual_action_fields():
    score = run_exam()
    assert score.cases
    for case in score.cases:
        assert case.name
        assert case.actual_action is not None


def test_markdown_scorecard_is_stable_and_readable():
    score = run_exam()
    md = render_markdown(score)
    assert md.startswith("# M0 Driving Exam Scorecard")
    assert "| Scenario | Result |" in md
    assert f"- Total: {score.total}" in md


def test_pass_rate_matches_case_results():
    score = run_exam()
    expected = 1.0 if score.total == 0 else score.passed / score.total
    assert score.pass_rate == expected
