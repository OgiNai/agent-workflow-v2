"""Deterministic evaluation scoring."""

from apps.schemas.tools import TestRunResult

LLM_CORRECTNESS_WEIGHT = 0.35
LLM_SECURITY_WEIGHT = 0.35
LLM_MAINTAINABILITY_WEIGHT = 0.30

RULE_SCORE_WEIGHT = 0.25
EXECUTION_SCORE_WEIGHT = 0.45
LLM_SCORE_WEIGHT = 0.30


def calculate_execution_score(test_result: TestRunResult) -> float:
    """Calculate an execution score from structured pytest results.

    Execution failures and timeouts are scored as zero. For a completed
    test run, the score is the proportion of passed tests. A run with no
    collected tests is considered unsuccessful.
    """

    if test_result.status in {"error", "timeout"}:
        return 0.0

    if test_result.tests_total <= 0:
        return 0.0

    return round(
        test_result.tests_passed / test_result.tests_total,
        3,
    )


def calculate_llm_score(
    *,
    correctness_score: float,
    security_score: float,
    maintainability_score: float,
) -> float:
    """Calculate the weighted qualitative LLM evaluation score."""

    return round(
        LLM_CORRECTNESS_WEIGHT * correctness_score
        + LLM_SECURITY_WEIGHT * security_score
        + LLM_MAINTAINABILITY_WEIGHT * maintainability_score,
        3,
    )


def calculate_final_score(
    *,
    rule_score: float,
    execution_score: float,
    llm_score: float,
) -> float:
    """Calculate the deterministic overall workflow score."""

    return round(
        RULE_SCORE_WEIGHT * rule_score
        + EXECUTION_SCORE_WEIGHT * execution_score
        + LLM_SCORE_WEIGHT * llm_score,
        3,
    )
