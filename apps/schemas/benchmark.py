"""Benchmark case schemas and expectation matching."""

from __future__ import annotations

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
