"""Deterministic evaluator for HIL validation evidence.

This module is offline/read-only. It does not control vehicle hardware.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class HILResult:
    test_id: str
    passed: bool
    critical: bool = True


@dataclass(frozen=True)
class HILGateResult:
    eligible_for_controlled_vehicle_test: bool
    failed_critical: tuple[str, ...]
    failed_noncritical: tuple[str, ...]
    total: int
    passed: int


def evaluate(results: tuple[HILResult, ...]) -> HILGateResult:
    failed_critical = tuple(r.test_id for r in results if not r.passed and r.critical)
    failed_noncritical = tuple(r.test_id for r in results if not r.passed and not r.critical)
    passed = sum(1 for r in results if r.passed)
    return HILGateResult(
        eligible_for_controlled_vehicle_test=(len(results) > 0 and not failed_critical),
        failed_critical=failed_critical,
        failed_noncritical=failed_noncritical,
        total=len(results),
        passed=passed,
    )
