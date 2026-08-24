"""M0 regression exam runner for the synthetic scenario library.

Offline/read-only. Runs deterministic scenarios through the current M0 stack and
compares observed advisory outputs with expected regression outcomes.
"""

from dataclasses import dataclass
from typing import Iterable

from simulation.scenarios.library import ScenarioSpec, scenario_library
from simulation.scenarios.scenario_runner import run_scenario


@dataclass(frozen=True)
class ExamCaseResult:
    name: str
    passed: bool
    expected_action: str | None
    actual_action: str | None
    expected_review_priority: str | None
    actual_review_priority: str | None
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class ExamScorecard:
    total: int
    passed: int
    failed: int
    pass_rate: float
    cases: tuple[ExamCaseResult, ...]


def run_case(spec: ScenarioSpec) -> ExamCaseResult:
    result = run_scenario(spec.input)
    actual_action = result.shadow_decision.action.value
    actual_priority = result.disagreement.priority

    action_ok = spec.expected_action is None or actual_action == spec.expected_action
    priority_ok = (
        spec.expected_review_priority is None
        or actual_priority == spec.expected_review_priority
    )
    passed = action_ok and priority_ok

    notes: list[str] = []
    if not action_ok:
        notes.append("ACTION_MISMATCH")
    if not priority_ok:
        notes.append("REVIEW_PRIORITY_MISMATCH")

    return ExamCaseResult(
        name=spec.name,
        passed=passed,
        expected_action=spec.expected_action,
        actual_action=actual_action,
        expected_review_priority=spec.expected_review_priority,
        actual_review_priority=actual_priority,
        notes=tuple(notes),
    )


def run_exam(specs: Iterable[ScenarioSpec] | None = None) -> ExamScorecard:
    specs = tuple(scenario_library() if specs is None else specs)
    cases = tuple(run_case(spec) for spec in specs)
    total = len(cases)
    passed = sum(1 for c in cases if c.passed)
    failed = total - passed
    pass_rate = 1.0 if total == 0 else passed / total
    return ExamScorecard(total, passed, failed, pass_rate, cases)


def render_markdown(scorecard: ExamScorecard) -> str:
    lines = [
        "# M0 Driving Exam Scorecard",
        "",
        f"- Total: {scorecard.total}",
        f"- Passed: {scorecard.passed}",
        f"- Failed: {scorecard.failed}",
        f"- Pass rate: {scorecard.pass_rate:.1%}",
        "",
        "| Scenario | Result | Expected action | Actual action | Expected review | Actual review |",
        "|---|---|---|---|---|---|",
    ]
    for case in scorecard.cases:
        lines.append(
            f"| {case.name} | {'PASS' if case.passed else 'FAIL'} | "
            f"{case.expected_action or '-'} | {case.actual_action or '-'} | "
            f"{case.expected_review_priority or '-'} | {case.actual_review_priority or '-'} |"
        )
    return "\n".join(lines) + "\n"
