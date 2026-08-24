"""Promotion gate for moving autonomy changes beyond Learning/Shadow.

This module is intentionally conservative. It only evaluates offline evidence and
never enables vehicle actuation by itself.
"""

from dataclasses import dataclass
from enum import Enum


class PromotionDecision(str, Enum):
    BLOCK = "BLOCK"
    SHADOW_ONLY = "SHADOW_ONLY"
    ELIGIBLE_FOR_NEXT_VALIDATION_STAGE = "ELIGIBLE_FOR_NEXT_VALIDATION_STAGE"


@dataclass(frozen=True)
class PromotionEvidence:
    exam_total: int
    exam_passed: int
    replay_total: int
    replay_improvements: int
    replay_regressions: int
    critical_regressions: int
    unresolved_cases: int
    jurisdiction_coverage: int
    required_jurisdictions: int
    scenario_coverage_ratio: float
    required_scenario_coverage_ratio: float = 0.95
    minimum_exam_pass_rate: float = 0.98
    minimum_replay_cases: int = 100


@dataclass(frozen=True)
class PromotionResult:
    decision: PromotionDecision
    reasons: tuple[str, ...]
    exam_pass_rate: float


def evaluate(e: PromotionEvidence) -> PromotionResult:
    reasons: list[str] = []
    exam_rate = 0.0 if e.exam_total <= 0 else e.exam_passed / e.exam_total

    if e.critical_regressions > 0:
        reasons.append("CRITICAL_REGRESSION_PRESENT")
    if e.replay_regressions > 0:
        reasons.append("REPLAY_REGRESSION_PRESENT")
    if exam_rate < e.minimum_exam_pass_rate:
        reasons.append("EXAM_PASS_RATE_TOO_LOW")
    if e.replay_total < e.minimum_replay_cases:
        reasons.append("REPLAY_COVERAGE_TOO_LOW")
    if e.scenario_coverage_ratio < e.required_scenario_coverage_ratio:
        reasons.append("SCENARIO_COVERAGE_TOO_LOW")
    if e.jurisdiction_coverage < e.required_jurisdictions:
        reasons.append("JURISDICTION_COVERAGE_INCOMPLETE")
    if e.unresolved_cases > 0:
        reasons.append("UNRESOLVED_CASES_PRESENT")

    if "CRITICAL_REGRESSION_PRESENT" in reasons or "REPLAY_REGRESSION_PRESENT" in reasons:
        return PromotionResult(PromotionDecision.BLOCK, tuple(reasons), exam_rate)

    if reasons:
        return PromotionResult(PromotionDecision.SHADOW_ONLY, tuple(reasons), exam_rate)

    return PromotionResult(
        PromotionDecision.ELIGIBLE_FOR_NEXT_VALIDATION_STAGE,
        ("ALL_OFFLINE_GATES_PASSED",),
        exam_rate,
    )
