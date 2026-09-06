"""Tests for the evaluation benchmark framework."""

from pathlib import Path
from uuid import uuid4

import pytest

from apps.evals.benchmark_runner import load_benchmark_cases, match_finding_expectations
from apps.schemas.agent_outputs import EvaluatorOutput, Finding
from apps.schemas.benchmark import (
    BenchmarkCase,
    BenchmarkExpectations,
    BenchmarkFindingExpectation,
)
from apps.schemas.responses import ReviewResponse

CASES_PATH = Path("benchmarks/cases")


def make_case(
    findings: list[BenchmarkFindingExpectation],
) -> BenchmarkCase:
    return BenchmarkCase(
        id="test-case",
        category="correctness",
        instruction="Review this code.",
        source_code="def example():\n    return 1\n",
        expectations=BenchmarkExpectations(
            findings=findings,
        ),
    )


def make_response(
    findings: list[Finding],
) -> ReviewResponse:
    evaluation = EvaluatorOutput(
        final_decision="pass",
        rule_score=1.0,
        execution_score=1.0,
        llm_score=1.0,
        security_score=1.0,
        maintainability_score=1.0,
        correctness_score=1.0,
        final_score=1.0,
        findings=findings,
        explanation="Evaluation completed.",
    )

    return ReviewResponse(
        workflow_run_id=uuid4(),
        status="completed",
        task_type="review_refactor",
        source_type="inline_code",
        final_decision="pass",
        summary="Completed.",
        final_code="def example():\n    return 1\n",
        evaluation=evaluation,
        rounds_executed=1,
    )


def test_load_benchmark_cases():
    cases = load_benchmark_cases(CASES_PATH)

    assert len(cases) >= 4
    assert len({case.id for case in cases}) == len(cases)


def test_benchmark_case_contains_expected_sections():
    cases = load_benchmark_cases(CASES_PATH)

    for case in cases:
        assert case.instruction
        assert case.source_code
        assert case.expectations is not None


def test_matching_finding_by_category_severity_and_description():
    case = make_case(
        [
            BenchmarkFindingExpectation(
                category="security",
                severity="HIGH",
                description_contains=["sql", "injection"],
            )
        ]
    )

    response = make_response(
        [
            Finding(
                id="finding-1",
                category="security",
                severity="HIGH",
                description="Possible SQL injection vulnerability.",
            )
        ]
    )

    matches = match_finding_expectations(case, response)

    assert len(matches) == 1
    assert matches[0].matched is True
    assert matches[0].matched_finding_id == "finding-1"


def test_finding_matching_is_case_insensitive():
    case = make_case(
        [
            BenchmarkFindingExpectation(
                category="SECURITY",
                description_contains=["SQL"],
            )
        ]
    )

    response = make_response(
        [
            Finding(
                id="finding-1",
                category="security",
                severity="HIGH",
                description="Possible sql injection.",
            )
        ]
    )

    matches = match_finding_expectations(case, response)

    assert matches[0].matched is True


def test_unmatched_finding_expectation_is_reported():
    case = make_case(
        [
            BenchmarkFindingExpectation(
                category="security",
                severity="CRITICAL",
                description_contains=["authentication"],
            )
        ]
    )

    response = make_response(
        [
            Finding(
                id="finding-1",
                category="security",
                severity="HIGH",
                description="Possible SQL injection.",
            )
        ]
    )

    matches = match_finding_expectations(case, response)

    assert matches[0].matched is False
    assert matches[0].matched_finding_id is None


def test_actual_finding_can_match_only_one_expectation():
    case = make_case(
        [
            BenchmarkFindingExpectation(
                category="security",
                description_contains=["sql"],
            ),
            BenchmarkFindingExpectation(
                category="security",
                description_contains=["injection"],
            ),
        ]
    )

    response = make_response(
        [
            Finding(
                id="finding-1",
                category="security",
                severity="HIGH",
                description="Possible SQL injection.",
            )
        ]
    )

    matches = match_finding_expectations(case, response)

    assert matches[0].matched is True
    assert matches[1].matched is False


def test_no_expected_findings_passes_when_evaluation_is_missing():
    case = make_case([])

    response = make_response([]).model_copy(update={"evaluation": None})

    matches = match_finding_expectations(case, response)

    assert matches == []


@pytest.mark.parametrize(
    "category",
    [
        "correctness",
        "security",
        "maintainability",
        "mixed",
    ],
)
def test_benchmark_categories_are_valid(category: str):
    case = BenchmarkCase(
        id=f"case-{category}",
        category=category,
        instruction="Review this code.",
        source_code="x = 1\n",
        expectations=BenchmarkExpectations(),
    )

    assert case.category == category
