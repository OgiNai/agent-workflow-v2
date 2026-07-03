"""Deterministic rule-based evaluation."""

from apps.schemas.agent_outputs import SecurityAuditOutput
from apps.tools.static_analyzer import find_dangerous_patterns


def calculate_rule_score(code: str, security: SecurityAuditOutput) -> tuple[float, list[str]]:
    """Calculate a lightweight rule score between 0 and 1."""
    score = 1.0
    notes: list[str] = []

    if not code.strip():
        score -= 0.6
        notes.append("Candidate code is empty.")

    dangerous_patterns = find_dangerous_patterns(code)
    if dangerous_patterns:
        score -= min(0.4, 0.1 * len(dangerous_patterns))
        notes.append(f"Dangerous patterns found: {', '.join(dangerous_patterns)}")

    if security.status == "FAILED":
        score -= 0.25
        notes.append("Security auditor returned FAILED.")

    if "```" in code:
        score -= 0.1
        notes.append("Candidate code still contains markdown fences.")

    return max(0.0, min(1.0, score)), notes
