from unittest.mock import AsyncMock

import pytest

from apps.agents.inspection_agent import InspectionAgent
from apps.integrations.github.models import GitHubChangedFile
from apps.schemas.agent_outputs import Finding, ReviewerOutput, SecurityAuditOutput
from apps.schemas.review_context import PRContext


def test_reviewer_findings_receive_stable_ids():
    finding = Finding(
        id="llm_generated_id",
        category="correctness",
        severity="MEDIUM",
        description="Missing input validation.",
    )
    review = ReviewerOutput(
        summary="Issue found.",
        findings=[finding],
    )

    normalized = InspectionAgent._normalize_findings(review)

    assert len(normalized.findings) == 1

    normalized_finding = normalized.findings[0]

    assert normalized_finding.id.startswith("finding_")
    assert normalized_finding.id != "llm_generated_id"
    assert normalized_finding.status == "unresolved"


def test_security_findings_receive_stable_ids():
    finding = Finding(
        id="llm_generated_id",
        category="security",
        severity="HIGH",
        description="User-controlled path can escape the project directory.",
    )
    audit = SecurityAuditOutput(findings=[finding])

    normalized = InspectionAgent._normalize_findings(audit)

    assert len(normalized.findings) == 1

    normalized_finding = normalized.findings[0]

    assert normalized_finding.id.startswith("finding_")
    assert normalized_finding.id != "llm_generated_id"
    assert normalized_finding.status == "unresolved"


def test_same_finding_content_produces_same_id():
    first = Finding(
        id="first",
        category="security",
        severity="HIGH",
        description="Path traversal risk.",
    )
    second = Finding(
        id="second",
        category="security",
        severity="HIGH",
        description="Path traversal risk.",
    )

    first_normalized = InspectionAgent._normalize_findings(
        SecurityAuditOutput(findings=[first])
    )
    second_normalized = InspectionAgent._normalize_findings(
        SecurityAuditOutput(findings=[second])
    )

    assert first_normalized.findings[0].id == second_normalized.findings[0].id


def test_finding_id_is_case_and_whitespace_normalized():
    first = Finding(
        id="first",
        category=" Security ",
        severity="HIGH",
        description="  Path traversal risk.  ",
    )
    second = Finding(
        id="second",
        category="security",
        severity="HIGH",
        description="path traversal risk.",
    )

    assert InspectionAgent._finding_id(first) == InspectionAgent._finding_id(second)


def test_inspection_forces_llm_resolved_status_back_to_unresolved():
    finding = Finding(
        id="llm_generated_id",
        category="correctness",
        severity="MEDIUM",
        description="Missing input validation.",
        status="resolved",
    )
    review = ReviewerOutput(
        summary="Issue found.",
        findings=[finding],
    )

    normalized = InspectionAgent._normalize_findings(review)

    assert normalized.findings[0].status == "unresolved"


@pytest.mark.anyio
async def test_inspection_agent_includes_review_context_in_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    review_context = PRContext(
        pull_request_number=42,
        title="Improve validation",
        body="Improve input validation.",
        base_ref="main",
        head_ref="feature/validation",
        base_sha="base-sha",
        head_sha="head-sha",
        changed_files=[
            GitHubChangedFile(
                path="apps/example.py",
                status="modified",
                additions=2,
                deletions=1,
                changes=3,
                patch="@@ -1 +1 @@",
            )
        ],
    )

    expected_output = ReviewerOutput(
        summary="No issues found.",
        findings=[],
    )

    run_structured = AsyncMock(
        return_value=(expected_output, 5),
    )

    agent = InspectionAgent()
    monkeypatch.setattr(agent, "_run_structured", run_structured)

    result, latency_ms = await agent.run(
        mode="reviewer",
        instruction="Review this file.",
        code="print('hello')",
        review_context=review_context,
    )

    assert result == expected_output
    assert latency_ms == 5

    payload = run_structured.await_args.kwargs["payload"]

    assert payload["review_context"] == review_context.model_dump(mode="json")
