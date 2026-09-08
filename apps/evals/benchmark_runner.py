"""Execute reproducible evaluation benchmark cases and generate reports."""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from apps.core.settings import get_llm_settings
from apps.llm.prompts import PROMPT_VERSIONS
from apps.schemas.benchmark import (
    BenchmarkAggregateMetrics,
    BenchmarkCase,
    BenchmarkCaseReport,
    BenchmarkCaseResult,
    BenchmarkFindingMatch,
    BenchmarkModelConfig,
    BenchmarkPromptConfig,
    BenchmarkReport,
)
from apps.schemas.requests import ReviewRequest
from apps.schemas.responses import ReviewResponse
from apps.workflows.code_workflow import CodeWorkflow

DEFAULT_CASES_PATH = Path("benchmarks/cases")
DEFAULT_REPORTS_PATH = Path("benchmarks/reports")


def match_finding_expectations(
    case: BenchmarkCase,
    response: ReviewResponse,
) -> list[BenchmarkFindingMatch]:
    """Match expected findings against evaluator findings.

    Matching is semantic rather than exact. A finding matches when its
    category is equal, its severity matches when specified, and every
    configured description keyword occurs in its description.

    Each actual finding can satisfy at most one expectation.
    """

    actual_findings = (
        response.evaluation.findings if response.evaluation is not None else []
    )

    used_finding_ids: set[str] = set()
    matches: list[BenchmarkFindingMatch] = []

    for expectation in case.expectations.findings:
        matched_finding = None

        for finding in actual_findings:
            if finding.id in used_finding_ids:
                continue

            if finding.category.lower() != expectation.category.lower():
                continue

            if (
                expectation.severity is not None
                and finding.severity != expectation.severity
            ):
                continue

            description = finding.description.lower()

            if any(
                keyword.lower() not in description
                for keyword in expectation.description_contains
            ):
                continue

            matched_finding = finding
            break

        if matched_finding is not None:
            used_finding_ids.add(matched_finding.id)
            matches.append(
                BenchmarkFindingMatch(
                    expectation=expectation,
                    matched_finding_id=matched_finding.id,
                    matched_description=matched_finding.description,
                    matched=True,
                )
            )
        else:
            matches.append(
                BenchmarkFindingMatch(
                    expectation=expectation,
                    matched=False,
                )
            )

    return matches


def load_benchmark_cases(
    cases_path: Path = DEFAULT_CASES_PATH,
) -> list[BenchmarkCase]:
    """Load and validate all benchmark cases below a directory."""

    if not cases_path.exists():
        raise FileNotFoundError(
            f"Benchmark cases directory does not exist: {cases_path}"
        )

    case_files = sorted(cases_path.rglob("*.json"))

    if not case_files:
        raise ValueError(f"No benchmark case files found under: {cases_path}")

    cases: list[BenchmarkCase] = []

    for case_file in case_files:
        with case_file.open("r", encoding="utf-8") as file:
            payload = json.load(file)

        cases.append(BenchmarkCase.model_validate(payload))

    case_ids = [case.id for case in cases]

    if len(case_ids) != len(set(case_ids)):
        raise ValueError("Benchmark case IDs must be unique.")

    return cases


async def run_benchmark(
    cases: list[BenchmarkCase],
) -> list[BenchmarkCaseResult]:
    """Execute all benchmark cases sequentially."""

    workflow = CodeWorkflow()
    results: list[BenchmarkCaseResult] = []

    for case in cases:
        request = ReviewRequest(
            task_type="review_refactor",
            instruction=case.instruction,
            code=case.source_code,
        )

        response = await workflow.run(request)

        finding_matches = match_finding_expectations(
            case,
            response,
        )

        results.append(
            BenchmarkCaseResult(
                case_id=case.id,
                case_version=case.version,
                category=case.category,
                workflow_run_id=response.workflow_run_id,
                response=response,
                finding_matches=finding_matches,
            )
        )

    return results


def build_benchmark_report(
    *,
    results: list[BenchmarkCaseResult],
    benchmark_run_id: UUID,
    started_at: datetime,
    completed_at: datetime,
    cases_path: Path,
) -> BenchmarkReport:
    """Build a structured report from completed benchmark results."""

    case_reports: list[BenchmarkCaseReport] = []

    for result in results:
        evaluation = result.response.evaluation

        test_result = None
        for step in result.response.steps:
            if step.step_name == "test_runner":
                test_result = step.metadata
                break

        findings = (
            [finding.model_dump(mode="json") for finding in evaluation.findings]
            if evaluation is not None
            else []
        )

        finding_resolution_rate = None

        if findings:
            resolved_findings = sum(
                finding["status"] == "resolved" for finding in findings
            )
            finding_resolution_rate = round(
                resolved_findings / len(findings),
                3,
            )

        case_duration_ms = sum(
            int(step.latency_ms)
            for step in result.response.steps
            if step.latency_ms is not None
        )

        case_reports.append(
            BenchmarkCaseReport(
                case_id=result.case_id,
                case_version=result.case_version,
                category=result.category,
                workflow_run_id=result.workflow_run_id,
                status=result.response.status,
                final_decision=result.response.final_decision,
                rounds_executed=result.response.rounds_executed,
                duration_ms=case_duration_ms,
                final_score=(
                    evaluation.final_score if evaluation is not None else None
                ),
                rule_score=(evaluation.rule_score if evaluation is not None else None),
                execution_score=(
                    evaluation.execution_score if evaluation is not None else None
                ),
                llm_score=(evaluation.llm_score if evaluation is not None else None),
                correctness_score=(
                    evaluation.correctness_score if evaluation is not None else None
                ),
                security_score=(
                    evaluation.security_score if evaluation is not None else None
                ),
                maintainability_score=(
                    evaluation.maintainability_score if evaluation is not None else None
                ),
                findings_expected=result.findings_total,
                findings_matched=result.findings_passed,
                finding_resolution_rate=finding_resolution_rate,
                findings=findings,
                test_result=test_result,
                finding_matches=result.finding_matches,
            )
        )

    final_scores = [
        case.final_score for case in case_reports if case.final_score is not None
    ]
    rule_scores = [
        case.rule_score for case in case_reports if case.rule_score is not None
    ]
    execution_scores = [
        case.execution_score
        for case in case_reports
        if case.execution_score is not None
    ]
    llm_scores = [case.llm_score for case in case_reports if case.llm_score is not None]
    correctness_scores = [
        case.correctness_score
        for case in case_reports
        if case.correctness_score is not None
    ]
    security_scores = [
        case.security_score for case in case_reports if case.security_score is not None
    ]
    maintainability_scores = [
        case.maintainability_score
        for case in case_reports
        if case.maintainability_score is not None
    ]

    total_expected_findings = sum(case.findings_expected for case in case_reports)
    total_matched_findings = sum(case.findings_matched for case in case_reports)

    total_findings = sum(len(case.findings) for case in case_reports)
    resolved_findings = sum(
        sum(finding["status"] == "resolved" for finding in case.findings)
        for case in case_reports
    )

    retry_cases = sum(case.rounds_executed > 1 for case in case_reports)

    total_duration_ms = sum(case.duration_ms or 0 for case in case_reports)

    cases_total = len(case_reports)

    aggregate = BenchmarkAggregateMetrics(
        cases_total=cases_total,
        cases_passed=sum(case.final_decision == "pass" for case in case_reports),
        cases_passed_with_warnings=sum(
            case.final_decision == "pass_with_warnings" for case in case_reports
        ),
        cases_retry=sum(case.final_decision == "retry" for case in case_reports),
        cases_failed=sum(case.status == "failed" for case in case_reports),
        average_final_score=(
            round(sum(final_scores) / len(final_scores), 3) if final_scores else None
        ),
        average_rule_score=(
            round(sum(rule_scores) / len(rule_scores), 3) if rule_scores else None
        ),
        average_execution_score=(
            round(sum(execution_scores) / len(execution_scores), 3)
            if execution_scores
            else None
        ),
        average_llm_score=(
            round(sum(llm_scores) / len(llm_scores), 3) if llm_scores else None
        ),
        average_correctness_score=(
            round(sum(correctness_scores) / len(correctness_scores), 3)
            if correctness_scores
            else None
        ),
        average_security_score=(
            round(sum(security_scores) / len(security_scores), 3)
            if security_scores
            else None
        ),
        average_maintainability_score=(
            round(
                sum(maintainability_scores) / len(maintainability_scores),
                3,
            )
            if maintainability_scores
            else None
        ),
        finding_resolution_rate=(
            round(resolved_findings / total_findings, 3) if total_findings else None
        ),
        finding_expectation_match_rate=(
            round(
                total_matched_findings / total_expected_findings,
                3,
            )
            if total_expected_findings
            else None
        ),
        retry_rate=(round(retry_cases / cases_total, 3) if cases_total else 0.0),
        total_duration_ms=total_duration_ms,
        average_case_duration_ms=(
            round(total_duration_ms / cases_total, 1) if cases_total else None
        ),
    )

    llm_settings = get_llm_settings()

    return BenchmarkReport(
        benchmark_run_id=benchmark_run_id,
        started_at=started_at,
        completed_at=completed_at,
        duration_ms=int((completed_at - started_at).total_seconds() * 1000),
        cases_path=str(cases_path),
        cases_total=cases_total,
        model=BenchmarkModelConfig(
            model_name=llm_settings.model_name,
            temperature=llm_settings.temperature,
            attempts=llm_settings.attempts,
            initial_delay=llm_settings.initial_delay,
        ),
        prompts=BenchmarkPromptConfig(
            versions=dict(PROMPT_VERSIONS),
        ),
        cases=case_reports,
        aggregate=aggregate,
    )


async def _main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the agent-workflow evaluation benchmark.",
    )
    parser.add_argument(
        "--cases-path",
        type=Path,
        default=DEFAULT_CASES_PATH,
        help="Directory containing benchmark case JSON files.",
    )
    parser.add_argument(
        "--reports-path",
        type=Path,
        default=DEFAULT_REPORTS_PATH,
        help="Directory where benchmark JSON reports are written.",
    )
    args = parser.parse_args()

    cases = load_benchmark_cases(args.cases_path)

    started_at = datetime.now(UTC)
    results = await run_benchmark(cases)
    completed_at = datetime.now(UTC)
    report = build_benchmark_report(
        results=results,
        benchmark_run_id=uuid4(),
        started_at=started_at,
        completed_at=completed_at,
        cases_path=args.cases_path,
    )

    args.reports_path.mkdir(parents=True, exist_ok=True)
    filename = (
        f"benchmark_"
        f"{started_at.strftime('%Y-%m-%dT%H%M%SZ')}_"
        f"{report.benchmark_run_id}.json"
    )
    report_path = args.reports_path / filename
    with report_path.open("w", encoding="utf-8") as file:
        json.dump(
            report.model_dump(mode="json"),
            file,
            indent=2,
        )
    print(f"Benchmark report written to: {report_path}")


if __name__ == "__main__":
    asyncio.run(_main())
