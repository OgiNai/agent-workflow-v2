"""Tests for deterministic evaluation scoring and decision policy."""

import pytest

from apps.evals.decision_policy import (
    PASS_THRESHOLD,
    determine_decision,
)
from apps.evals.scoring import (
    calculate_execution_score,
    calculate_final_score,
    calculate_llm_score,
)
from apps.schemas.agent_outputs import Finding
from apps.schemas.tools import TestRunResult


def make_test_result(
    *,
    status: str = "passed",
    total: int = 10,
    passed: int = 10,
    failed: int = 0,
    skipped: int = 0,
    xfailed: int = 0,
    xpassed: int = 0,
) -> TestRunResult:
    return TestRunResult(
        status=status,
        tests_total=total,
        tests_passed=passed,
        tests_failed=failed,
        tests_skipped=skipped,
        tests_xfailed=xfailed,
        tests_xpassed=xpassed,
        duration_ms=100,
    )


def make_finding(
    finding_id: str,
    *,
    severity: str = "MEDIUM",
    status: str = "unresolved",
) -> Finding:
    return Finding(
        id=finding_id,
        category="correctness",
        severity=severity,
        description="Test finding.",
        status=status,
    )


def test_execution_score_all_tests_pass():
    result = make_test_result(total=5, passed=5)

    assert calculate_execution_score(result) == 1.0


def test_execution_score_is_passed_over_total():
    result = make_test_result(
        total=10,
        passed=7,
        failed=3,
    )

    assert calculate_execution_score(result) == 0.7


def test_execution_score_zero_when_no_tests_are_collected():
    result = make_test_result(total=0, passed=0)

    assert calculate_execution_score(result) == 0.0


@pytest.mark.parametrize("status", ["error", "timeout"])
def test_execution_score_zero_for_execution_error(status: str):
    result = make_test_result(
        status=status,
        total=5,
        passed=5,
    )

    assert calculate_execution_score(result) == 0.0


def test_execution_score_does_not_penalize_skipped_tests():
    result = make_test_result(
        total=5,
        passed=3,
        skipped=2,
    )

    assert calculate_execution_score(result) == 0.6


def test_execution_score_does_not_penalize_xfailed_tests():
    result = make_test_result(
        total=5,
        passed=4,
        xfailed=1,
    )

    assert calculate_execution_score(result) == 0.8


def test_execution_score_does_not_penalize_xpassed_tests():
    result = make_test_result(
        total=5,
        passed=4,
        xpassed=1,
    )

    assert calculate_execution_score(result) == 0.8


def test_llm_score_uses_agreed_weights():
    score = calculate_llm_score(
        correctness_score=1.0,
        security_score=0.8,
        maintainability_score=0.6,
    )

    assert score == 0.81


def test_final_score_uses_agreed_weights():
    score = calculate_final_score(
        rule_score=1.0,
        execution_score=0.8,
        llm_score=0.6,
    )

    assert score == 0.79


def test_final_score_exactly_at_threshold():
    result = make_test_result()

    assert (
        determine_decision(
            final_score=PASS_THRESHOLD,
            test_result=result,
            findings=[],
        )
        == "pass"
    )


def test_final_score_just_below_threshold():
    result = make_test_result()

    assert (
        determine_decision(
            final_score=PASS_THRESHOLD - 0.001,
            test_result=result,
            findings=[],
        )
        == "retry"
    )


@pytest.mark.parametrize("severity", ["HIGH", "CRITICAL"])
def test_blocking_unresolved_finding_forces_retry(severity: str):
    result = make_test_result()

    assert (
        determine_decision(
            final_score=1.0,
            test_result=result,
            findings=[make_finding("finding_1", severity=severity)],
        )
        == "retry"
    )


@pytest.mark.parametrize("severity", ["HIGH", "CRITICAL"])
def test_resolved_blocking_finding_does_not_force_retry(severity: str):
    result = make_test_result()

    assert (
        determine_decision(
            final_score=1.0,
            test_result=result,
            findings=[
                make_finding(
                    "finding_1",
                    severity=severity,
                    status="resolved",
                )
            ],
        )
        == "pass"
    )


@pytest.mark.parametrize("severity", ["LOW", "MEDIUM"])
def test_unresolved_non_blocking_finding_produces_warning(severity: str):
    result = make_test_result()

    assert (
        determine_decision(
            final_score=1.0,
            test_result=result,
            findings=[make_finding("finding_1", severity=severity)],
        )
        == "pass_with_warnings"
    )


@pytest.mark.parametrize("status", ["failed", "error", "timeout"])
def test_execution_failure_forces_retry(status: str):
    result = make_test_result(status=status)

    assert (
        determine_decision(
            final_score=1.0,
            test_result=result,
            findings=[],
        )
        == "retry"
    )


def test_no_tests_force_retry_through_execution_score():
    result = make_test_result(
        total=0,
        passed=0,
    )

    execution_score = calculate_execution_score(result)

    assert execution_score == 0.0

    assert (
        determine_decision(
            final_score=0.0,
            test_result=result,
            findings=[],
        )
        == "retry"
    )


def test_high_score_cannot_override_blocking_finding():
    result = make_test_result()

    assert (
        determine_decision(
            final_score=1.0,
            test_result=result,
            findings=[
                make_finding(
                    "finding_1",
                    severity="CRITICAL",
                )
            ],
        )
        == "retry"
    )


def test_high_score_with_only_warnings_passes_with_warnings():
    result = make_test_result()

    assert (
        determine_decision(
            final_score=1.0,
            test_result=result,
            findings=[
                make_finding(
                    "finding_1",
                    severity="LOW",
                ),
                make_finding(
                    "finding_2",
                    severity="MEDIUM",
                ),
            ],
        )
        == "pass_with_warnings"
    )
