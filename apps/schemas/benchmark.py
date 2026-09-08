"""Benchmark case schemas and expectation matching."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from apps.schemas.responses import ReviewResponse

BenchmarkCategory = Literal[
    "correctness",
    "security",
    "maintainability",
    "mixed",
]

FindingSeverity = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


class BenchmarkFindingExpectation(BaseModel):
    """Expected properties of a finding produced by the workflow."""

    category: str
    severity: FindingSeverity | None = None
    description_contains: list[str] = Field(default_factory=list)


class BenchmarkExpectations(BaseModel):
    """Expected semantic properties of a benchmark case."""

    findings: list[BenchmarkFindingExpectation] = Field(default_factory=list)
    behavior: list[str] = Field(default_factory=list)
    security: list[str] = Field(default_factory=list)
    tests: list[str] = Field(default_factory=list)


class BenchmarkCase(BaseModel):
    """A reproducible benchmark input and its expected outcomes."""

    id: str
    version: str = "1"
    category: BenchmarkCategory
    instruction: str
    source_code: str
    expectations: BenchmarkExpectations


class BenchmarkFindingMatch(BaseModel):
    """Result of matching one expected finding against actual findings."""

    expectation: BenchmarkFindingExpectation
    matched_finding_id: str | None = None
    matched_description: str | None = None
    matched: bool


class BenchmarkCaseResult(BaseModel):
    """Structured result produced by executing one benchmark case."""

    case_id: str
    case_version: str
    category: BenchmarkCategory
    workflow_run_id: UUID
    response: ReviewResponse
    finding_matches: list[BenchmarkFindingMatch] = Field(default_factory=list)

    @property
    def findings_passed(self) -> int:
        """Return the number of finding expectations that were satisfied."""
        return sum(match.matched for match in self.finding_matches)

    @property
    def findings_total(self) -> int:
        """Return the total number of finding expectations."""
        return len(self.finding_matches)

    @property
    def findings_all_matched(self) -> bool:
        """Return whether every expected finding was identified."""
        return all(match.matched for match in self.finding_matches)


class BenchmarkModelConfig(BaseModel):
    """Non-sensitive LLM configuration captured by a benchmark report."""

    model_name: str
    temperature: float
    attempts: int
    initial_delay: float


class BenchmarkPromptConfig(BaseModel):
    """Prompt versions used by the benchmark workflow."""

    versions: dict[str, str] = Field(default_factory=dict)


class BenchmarkCaseReport(BaseModel):
    """Evaluation results for one benchmark case."""

    case_id: str
    case_version: str
    category: BenchmarkCategory
    workflow_run_id: UUID

    status: str
    final_decision: str
    rounds_executed: int
    duration_ms: int | None = None

    final_score: float | None = None
    rule_score: float | None = None
    execution_score: float | None = None
    llm_score: float | None = None
    correctness_score: float | None = None
    security_score: float | None = None
    maintainability_score: float | None = None

    findings_expected: int
    findings_matched: int
    finding_resolution_rate: float | None = None
    findings: list[dict] = Field(default_factory=list)

    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None

    test_result: dict | None = None
    finding_matches: list[BenchmarkFindingMatch] = Field(default_factory=list)


class BenchmarkAggregateMetrics(BaseModel):
    """Aggregate metrics for one benchmark run."""

    cases_total: int
    cases_passed: int
    cases_passed_with_warnings: int
    cases_retry: int
    cases_failed: int

    average_final_score: float | None = None
    average_rule_score: float | None = None
    average_execution_score: float | None = None
    average_llm_score: float | None = None
    average_correctness_score: float | None = None
    average_security_score: float | None = None
    average_maintainability_score: float | None = None

    finding_resolution_rate: float | None = None
    finding_expectation_match_rate: float | None = None
    retry_rate: float = 0.0

    average_prompt_tokens: float | None = None
    average_completion_tokens: float | None = None
    average_total_tokens: float | None = None

    total_duration_ms: int = 0
    average_case_duration_ms: float | None = None


class BenchmarkReport(BaseModel):
    """Complete structured report for one benchmark execution."""

    report_version: str = "1"
    benchmark_run_id: UUID
    started_at: datetime
    completed_at: datetime
    duration_ms: int

    cases_path: str
    cases_total: int

    model: BenchmarkModelConfig
    prompts: BenchmarkPromptConfig

    cases: list[BenchmarkCaseReport] = Field(default_factory=list)
    aggregate: BenchmarkAggregateMetrics
