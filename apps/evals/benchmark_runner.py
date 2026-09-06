"""Execute reproducible evaluation benchmark cases."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from apps.schemas.benchmark import (
    BenchmarkCase,
    BenchmarkCaseResult,
    BenchmarkFindingMatch,
)
from apps.schemas.requests import ReviewRequest
from apps.schemas.responses import ReviewResponse
from apps.workflows.code_workflow import CodeWorkflow

DEFAULT_CASES_PATH = Path("benchmarks/cases")


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
    args = parser.parse_args()

    cases = load_benchmark_cases(args.cases_path)
    results = await run_benchmark(cases)

    payload = [result.model_dump(mode="json") for result in results]

    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    asyncio.run(_main())
