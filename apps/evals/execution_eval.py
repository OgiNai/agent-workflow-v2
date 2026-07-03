"""Execution-based evaluation."""

from apps.tools.test_runner import TestRunResult


def calculate_execution_score(test_result: TestRunResult) -> float:
    if test_result.status == "passed":
        return 1.0
    if test_result.status == "failed":
        return 0.35
    if test_result.status == "timeout":
        return 0.0
    return 0.1
