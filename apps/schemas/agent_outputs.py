"""Structured outputs returned by agents."""

from typing import Literal

from pydantic import BaseModel, Field


class Finding(BaseModel):
    """Normalized inspection finding tracked through evaluation."""

    id: str = Field(description="Stable identifier assigned by the application.")
    category: str = Field(
        description="Finding category, such as correctness, security, or maintainability."
    )
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = Field(
        description="Severity of the finding."
    )
    description: str = Field(description="Concise description of the issue.")
    status: Literal["unresolved", "resolved"] = Field(
        default="unresolved",
        description="Whether the finding remains present in the current candidate.",
    )


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
    findings: list[Finding] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    risk_level: Literal["LOW", "MEDIUM", "HIGH"] = "LOW"

    @property
    def issues(self) -> list[str]:
        """Return finding descriptions for backward-compatible consumers."""
        return [finding.description for finding in self.findings]


class SecurityAuditOutput(BaseModel):
    findings: list[Finding] = Field(default_factory=list)
    notes: str | None = None

    @property
    def status(self) -> Literal["PASSED", "FAILED"]:
        """Return aggregate status for backward-compatible consumers."""
        return (
            "FAILED"
            if any(finding.status == "unresolved" for finding in self.findings)
            else "PASSED"
        )

    @property
    def severity(self) -> Literal["NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"]:
        """Return the highest current unresolved severity."""
        severities = {
            "NONE": 0,
            "LOW": 1,
            "MEDIUM": 2,
            "HIGH": 3,
            "CRITICAL": 4,
        }

        unresolved = [
            finding.severity
            for finding in self.findings
            if finding.status == "unresolved"
        ]

        if not unresolved:
            return "NONE"

        return max(
            unresolved,
            key=lambda severity: severities[severity],
        )

    @property
    def vulnerabilities(self) -> list[str]:
        """Return unresolved security finding descriptions."""
        return [
            finding.description
            for finding in self.findings
            if finding.status == "unresolved"
        ]

    @property
    def required_fixes(self) -> list[str]:
        """Return unresolved security finding descriptions."""
        return self.vulnerabilities


class TestGeneratorOutput(BaseModel):
    # disable pytest for that class
    __test__ = False

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
    findings: list[Finding] = Field(
        default_factory=list,
        description=(
            "Original reviewer and security findings with their current "
            "resolved/unresolved status."
        ),
    )
    reasons: list[str] = Field(default_factory=list)
    retry_feedback: str | None = None
