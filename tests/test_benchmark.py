"""Tests for the evaluation benchmark framework."""

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from apps.evals.benchmark_runner import (
    build_benchmark_report,
    load_benchmark_cases,
    match_finding_expectations,
)
from apps.schemas.agent_outputs import EvaluatorOutput, Finding
from apps.schemas.benchmark import (
    BenchmarkCase,
    BenchmarkCaseReport,
    BenchmarkCaseResult,
    BenchmarkExpectations,
    BenchmarkFindingExpectation,
)
from apps.schemas.responses import ReviewResponse
from apps.schemas.workflow import WorkflowStepTrace

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


def test_build_benchmark_report_contains_aggregate_metrics():
    case = make_case([])

    response = make_response([])

    result = BenchmarkCaseResult(
        case_id=case.id,
        case_version=case.version,
        category=case.category,
        workflow_run_id=response.workflow_run_id,
        response=response,
        finding_matches=[],
    )

    started_at = datetime.now(UTC)
    completed_at = datetime.now(UTC)

    report = build_benchmark_report(
        results=[result],
        benchmark_run_id=uuid4(),
        started_at=started_at,
        completed_at=completed_at,
        cases_path=CASES_PATH,
    )

    assert report.cases_total == 1
    assert report.aggregate.cases_total == 1
    assert report.aggregate.cases_passed == 1
    assert report.aggregate.average_final_score == 1.0
    assert report.aggregate.finding_expectation_match_rate is None
    assert report.model.model_name
    assert report.prompts.versions


def test_build_benchmark_report_extracts_test_result():
    case = make_case([])

    response = make_response([]).model_copy(
        update={
            "steps": [
                WorkflowStepTrace(
                    step_name="test_runner",
                    step_type="tool",
                    status="success",
                    latency_ms=25,
                    metadata={
                        "status": "passed",
                        "tests_total": 2,
                        "tests_passed": 2,
                    },
                )
            ]
        }
    )

    result = BenchmarkCaseResult(
        case_id=case.id,
        case_version=case.version,
        category=case.category,
        workflow_run_id=response.workflow_run_id,
        response=response,
        finding_matches=[],
    )

    report = build_benchmark_report(
        results=[result],
        benchmark_run_id=uuid4(),
        started_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
        cases_path=CASES_PATH,
    )

    assert report.cases[0].test_result is not None
    assert report.cases[0].test_result["status"] == "passed"
    assert report.cases[0].duration_ms == 25


def test_benchmark_case_report_contains_token_usage() -> None:
    """Benchmark case reports should expose workflow token usage."""

    report = BenchmarkCaseReport(
        case_id="case-1",
        case_version="1",
        category="correctness",
        workflow_run_id=uuid4(),
        status="completed",
        final_decision="pass",
        rounds_executed=1,
        findings_expected=0,
        findings_matched=0,
        prompt_tokens=1200,
        completion_tokens=800,
        total_tokens=2000,
    )

    assert report.prompt_tokens == 1200
    assert report.completion_tokens == 800
    assert report.total_tokens == 2000


def test_benchmark_report_averages_token_usage() -> None:
    response = ReviewResponse(
        workflow_run_id=uuid4(),
        task_type="review_refactor",
        source_type="inline_code",
        summary="none",
        status="completed",
        final_decision="pass",
        rounds_executed=1,
        steps=[
            WorkflowStepTrace(
                step_name="reviewer",
                step_type="agent",
                status="success",
                metadata={
                    "prompt_tokens": 100,
                    "completion_tokens": 50,
                    "total_tokens": 150,
                },
            ),
            WorkflowStepTrace(
                step_name="security_auditor",
                step_type="agent",
                status="success",
                metadata={
                    "prompt_tokens": 200,
                    "completion_tokens": 100,
                    "total_tokens": 300,
                },
            ),
        ],
    )

    result = BenchmarkCaseResult(
        case_id="token-test",
        case_version="1.0",
        category="correctness",
        workflow_run_id=uuid4(),
        response=response,
        findings_total=0,
        findings_passed=0,
        finding_matches=[],
    )

    report = build_benchmark_report(
        results=[result],
        benchmark_run_id=uuid4(),
        started_at=datetime(2026, 1, 1, tzinfo=UTC),
        completed_at=datetime(2026, 1, 1, 0, 0, 1, tzinfo=UTC),
        cases_path=Path("benchmarks/cases"),
    )

    case = report.cases[0]

    assert case.prompt_tokens == 300
    assert case.completion_tokens == 150
    assert case.total_tokens == 450

    assert report.aggregate.average_prompt_tokens == 150.0
    assert report.aggregate.average_completion_tokens == 75.0
    assert report.aggregate.average_total_tokens == 225.0
