"""Compare and present evaluation benchmark reports."""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from apps.schemas.benchmark import BenchmarkAggregateMetrics, BenchmarkReport


@dataclass(frozen=True)
class MetricComparison:
    """Comparison of one benchmark metric."""

    name: str
    baseline: float | None
    candidate: float | None
    delta: float | None


@dataclass(frozen=True)
class BenchmarkComparison:
    """Comparison between two benchmark reports."""

    baseline_run_id: str
    candidate_run_id: str
    metrics: tuple[MetricComparison, ...]


def compare_benchmark_reports(
    baseline: BenchmarkReport,
    candidate: BenchmarkReport,
) -> BenchmarkComparison:
    """Compare aggregate metrics between two benchmark reports."""

    aggregate_pairs: tuple[
        tuple[str, Callable[[BenchmarkAggregateMetrics], float | None]],
        ...,
    ] = (
        ("final_score", lambda aggregate: aggregate.average_final_score),
        ("rule_score", lambda aggregate: aggregate.average_rule_score),
        ("execution_score", lambda aggregate: aggregate.average_execution_score),
        ("correctness", lambda aggregate: aggregate.average_correctness_score),
        ("security", lambda aggregate: aggregate.average_security_score),
        (
            "maintainability",
            lambda aggregate: aggregate.average_maintainability_score,
        ),
        (
            "finding_resolution_rate",
            lambda aggregate: aggregate.finding_resolution_rate,
        ),
        ("retry_rate", lambda aggregate: aggregate.retry_rate),
        (
            "average_case_duration_ms",
            lambda aggregate: aggregate.average_case_duration_ms,
        ),
        (
            "average_prompt_tokens",
            lambda aggregate: aggregate.average_prompt_tokens,
        ),
        (
            "average_completion_tokens",
            lambda aggregate: aggregate.average_completion_tokens,
        ),
        (
            "average_total_tokens",
            lambda aggregate: aggregate.average_total_tokens,
        ),
    )

    metrics: list[MetricComparison] = []

    for name, get_value in aggregate_pairs:
        baseline_value = get_value(baseline.aggregate)
        candidate_value = get_value(candidate.aggregate)

        delta = (
            round(candidate_value - baseline_value, 6)
            if baseline_value is not None and candidate_value is not None
            else None
        )

        metrics.append(
            MetricComparison(
                name=name,
                baseline=baseline_value,
                candidate=candidate_value,
                delta=delta,
            )
        )

    return BenchmarkComparison(
        baseline_run_id=str(baseline.benchmark_run_id),
        candidate_run_id=str(candidate.benchmark_run_id),
        metrics=tuple(metrics),
    )


def format_benchmark_comparison(
    comparison: BenchmarkComparison,
) -> str:
    """Format a benchmark comparison as a human-readable table."""

    lines = [
        "Benchmark Comparison",
        "====================",
        f"Baseline:  {comparison.baseline_run_id}",
        f"Candidate: {comparison.candidate_run_id}",
        "",
        (f"{'Metric':<32}{'Baseline':>12}{'Candidate':>12}{'Delta':>12}"),
        "-" * 68,
    ]

    for metric in comparison.metrics:
        baseline = f"{metric.baseline:.3f}" if metric.baseline is not None else "N/A"
        candidate = f"{metric.candidate:.3f}" if metric.candidate is not None else "N/A"
        delta = f"{metric.delta:+.3f}" if metric.delta is not None else "N/A"

        lines.append(f"{metric.name:<32}{baseline:>12}{candidate:>12}{delta:>12}")

    return "\n".join(lines)


def _main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare two agent-workflow benchmark reports.",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        required=True,
        help="Path to the baseline benchmark JSON report.",
    )
    parser.add_argument(
        "--candidate",
        type=Path,
        required=True,
        help="Path to the candidate benchmark JSON report.",
    )
    args = parser.parse_args()

    with args.baseline.open("r", encoding="utf-8") as file:
        baseline = BenchmarkReport.model_validate(json.load(file))

    with args.candidate.open("r", encoding="utf-8") as file:
        candidate = BenchmarkReport.model_validate(json.load(file))

    comparison = compare_benchmark_reports(baseline, candidate)
    print(format_benchmark_comparison(comparison))


if __name__ == "__main__":
    _main()
