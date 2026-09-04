"""Deterministic workflow evaluation decision policy."""

from typing import Literal

from apps.schemas.agent_outputs import Finding
from apps.schemas.tools import TestRunResult

EvaluationDecision = Literal[
    "pass",
    "pass_with_warnings",
    "retry",
]

PASS_THRESHOLD = 0.60

BLOCKING_SEVERITIES = {"HIGH", "CRITICAL"}
WARNING_SEVERITIES = {"LOW", "MEDIUM"}


def determine_decision(
    *,
    final_score: float,
    test_result: TestRunResult,
    findings: list[Finding],
) -> EvaluationDecision:
    """Determine the authoritative workflow decision.

    The decision is deterministic and does not depend on the LLM's proposed
    final decision or on the workflow's retry limit.

    Decision precedence:

    1. Execution failure/error/timeout -> retry.
    2. Unresolved HIGH/CRITICAL finding -> retry.
    3. Final score below threshold -> retry.
    4. Unresolved LOW/MEDIUM findings -> pass_with_warnings.
    5. Otherwise -> pass.
    """

    if test_result.status in {"failed", "error", "timeout"}:
        return "retry"

    if _has_unresolved_blocking_finding(findings):
        return "retry"

    if final_score < PASS_THRESHOLD:
        return "retry"

    if _has_unresolved_warning(findings):
        return "pass_with_warnings"

    return "pass"


def _has_unresolved_blocking_finding(
    findings: list[Finding],
) -> bool:
    """Return whether any unresolved finding has blocking severity."""

    return any(
        finding.status == "unresolved" and finding.severity in BLOCKING_SEVERITIES
        for finding in findings
    )


def _has_unresolved_warning(
    findings: list[Finding],
) -> bool:
    """Return whether any unresolved non-blocking finding remains."""

    return any(
        finding.status == "unresolved" and finding.severity in WARNING_SEVERITIES
        for finding in findings
    )
