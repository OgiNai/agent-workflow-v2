"""Tests for benchmark report comparison."""

from datetime import UTC, datetime
from uuid import uuid4

from apps.evals.benchmark_compare import (
    BenchmarkComparison,
    MetricComparison,
    compare_benchmark_reports,
    format_benchmark_comparison,
)
from apps.schemas.benchmark import (
    BenchmarkAggregateMetrics,
    BenchmarkReport,
)


def make_report(
    aggregate: BenchmarkAggregateMetrics,
) -> BenchmarkReport:
    """Create a minimal benchmark report for comparison tests."""

    return BenchmarkReport(
        benchmark_run_id=uuid4(),
        started_at=datetime(2026, 1, 1, tzinfo=UTC),
        completed_at=datetime(2026, 1, 1, 0, 0, 1, tzinfo=UTC),
        duration_ms=1000,
        cases_path="benchmarks/cases",
        cases_total=4,
        model={
            "model_name": "test-model",
            "temperature": 0.0,
            "attempts": 1,
            "initial_delay": 0.0,
        },
        prompts={
            "versions": {
                "reviewer": "1",
                "security_auditor": "1",
                "code_writer": "1",
                "test_generator": "1",
                "evaluator": "1",
            }
        },
        cases=[],
        aggregate=aggregate,
    )


def test_compare_benchmark_reports_calculates_metric_deltas() -> None:
    baseline = make_report(
        BenchmarkAggregateMetrics(
            cases_total=4,
            cases_passed=2,
            cases_passed_with_warnings=1,
            cases_retry=1,
            cases_failed=0,
            average_final_score=0.700,
            average_rule_score=0.800,
            average_execution_score=0.600,
            average_correctness_score=0.700,
            average_security_score=0.750,
            average_maintainability_score=0.650,
            finding_resolution_rate=0.750,
            retry_rate=0.500,
            average_case_duration_ms=8000.0,
            average_prompt_tokens=3000.0,
            average_completion_tokens=1000.0,
            average_total_tokens=4000.0,
        )
    )

    candidate = make_report(
        BenchmarkAggregateMetrics(
            cases_total=4,
            cases_passed=3,
            cases_passed_with_warnings=1,
            cases_retry=0,
            cases_failed=0,
            average_final_score=0.800,
            average_rule_score=0.850,
            average_execution_score=0.750,
            average_correctness_score=0.800,
            average_security_score=0.850,
            average_maintainability_score=0.750,
            finding_resolution_rate=0.875,
            retry_rate=0.250,
            average_case_duration_ms=7500.0,
            average_prompt_tokens=2800.0,
            average_completion_tokens=900.0,
            average_total_tokens=3700.0,
        )
    )

    comparison = compare_benchmark_reports(baseline, candidate)

    assert isinstance(comparison, BenchmarkComparison)
    assert comparison.baseline_run_id == str(baseline.benchmark_run_id)
    assert comparison.candidate_run_id == str(candidate.benchmark_run_id)

    assert comparison.metrics == (
        MetricComparison(
            name="final_score",
            baseline=0.700,
            candidate=0.800,
            delta=0.100,
        ),
        MetricComparison(
            name="rule_score",
            baseline=0.800,
            candidate=0.850,
            delta=0.050,
        ),
        MetricComparison(
            name="execution_score",
            baseline=0.600,
            candidate=0.750,
            delta=0.150,
        ),
        MetricComparison(
            name="correctness",
            baseline=0.700,
            candidate=0.800,
            delta=0.100,
        ),
        MetricComparison(
            name="security",
            baseline=0.750,
            candidate=0.850,
            delta=0.100,
        ),
        MetricComparison(
            name="maintainability",
            baseline=0.650,
            candidate=0.750,
            delta=0.100,
        ),
        MetricComparison(
            name="finding_resolution_rate",
            baseline=0.750,
            candidate=0.875,
            delta=0.125,
        ),
        MetricComparison(
            name="retry_rate",
            baseline=0.500,
            candidate=0.250,
            delta=-0.250,
        ),
        MetricComparison(
            name="average_case_duration_ms",
            baseline=8000.0,
            candidate=7500.0,
            delta=-500.0,
        ),
        MetricComparison(
            name="average_prompt_tokens",
            baseline=3000.0,
            candidate=2800.0,
            delta=-200.0,
        ),
        MetricComparison(
            name="average_completion_tokens",
            baseline=1000.0,
            candidate=900.0,
            delta=-100.0,
        ),
        MetricComparison(
            name="average_total_tokens",
            baseline=4000.0,
            candidate=3700.0,
            delta=-300.0,
        ),
    )


def test_compare_benchmark_reports_preserves_missing_metrics() -> None:
    baseline = make_report(
        BenchmarkAggregateMetrics(
            cases_total=1,
            cases_passed=1,
            cases_passed_with_warnings=0,
            cases_retry=0,
            cases_failed=0,
            average_final_score=0.8,
        )
    )

    candidate = make_report(
        BenchmarkAggregateMetrics(
            cases_total=1,
            cases_passed=1,
            cases_passed_with_warnings=0,
            cases_retry=0,
            cases_failed=0,
            average_final_score=0.9,
        )
    )

    comparison = compare_benchmark_reports(baseline, candidate)

    final_score = comparison.metrics[0]

    assert final_score.baseline == 0.8
    assert final_score.candidate == 0.9
    assert final_score.delta == 0.1

    assert comparison.metrics[1].baseline is None
    assert comparison.metrics[1].candidate is None
    assert comparison.metrics[1].delta is None


def test_format_benchmark_comparison() -> None:
    comparison = BenchmarkComparison(
        baseline_run_id="baseline-run",
        candidate_run_id="candidate-run",
        metrics=(
            MetricComparison(
                name="final_score",
                baseline=0.700,
                candidate=0.800,
                delta=0.100,
            ),
            MetricComparison(
                name="retry_rate",
                baseline=0.500,
                candidate=0.250,
                delta=-0.250,
            ),
        ),
    )

    formatted = format_benchmark_comparison(comparison)

    assert "Benchmark Comparison" in formatted
    assert "Baseline:  baseline-run" in formatted
    assert "Candidate: candidate-run" in formatted
    assert "final_score" in formatted
    assert "0.700" in formatted
    assert "0.800" in formatted
    assert "+0.100" in formatted
    assert "retry_rate" in formatted
    assert "-0.250" in formatted


def test_format_benchmark_comparison_handles_missing_metrics() -> None:
    comparison = BenchmarkComparison(
        baseline_run_id="baseline-run",
        candidate_run_id="candidate-run",
        metrics=(
            MetricComparison(
                name="security",
                baseline=None,
                candidate=None,
                delta=None,
            ),
        ),
    )

    formatted = format_benchmark_comparison(comparison)

    assert "security" in formatted
    assert formatted.count("N/A") == 3
