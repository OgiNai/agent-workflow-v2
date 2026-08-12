"""Structured outputs returned by agents."""

from typing import Literal

from pydantic import BaseModel, Field


class PlannerOutput(BaseModel):
    task_type: Literal["generate", "review_refactor"]
    requires_generation: bool
    requires_refactor: bool = True
    requires_tests: bool = True
    steps: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class CodeWriterOutput(BaseModel):
    code: str = Field(
        description="Complete corrected Python code only, without markdown fences."
    )
    explanation: str = Field(
        description="Short explanation of the implementation or changes."
    )
    changed_behavior_warnings: list[str] = Field(default_factory=list)


class ReviewerOutput(BaseModel):
    summary: str
    issues: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    risk_level: Literal["LOW", "MEDIUM", "HIGH"] = "LOW"


class SecurityAuditOutput(BaseModel):
    status: Literal["PASSED", "FAILED"]
    severity: Literal["NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
    vulnerabilities: list[str] = Field(default_factory=list)
    required_fixes: list[str] = Field(default_factory=list)
    notes: str | None = None


class TestGeneratorOutput(BaseModel):
    tests: str = Field(
        description="Complete pytest test module code, without markdown fences."
    )
    coverage_notes: list[str] = Field(default_factory=list)


class EvaluatorOutput(BaseModel):
    final_decision: Literal["pass", "pass_with_warnings", "retry"]
    rule_score: float = Field(ge=0, le=1)
    execution_score: float = Field(ge=0, le=1)
    llm_score: float | None = None  # llm_score: float = Field(ge=0, le=1)
    security_score: float = Field(ge=0, le=1)
    maintainability_score: float = Field(ge=0, le=1)
    correctness_score: float = Field(ge=0, le=1)
    final_score: float | None = None  # final_score: float = Field(ge=0, le=1)
    reasons: list[str] = Field(default_factory=list)
    retry_feedback: str | None = None
