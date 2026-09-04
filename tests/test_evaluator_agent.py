from apps.agents.evaluator_agent import EvaluatorAgent
from apps.schemas.agent_outputs import EvaluatorOutput, Finding


def make_finding(
    finding_id: str,
    *,
    category: str = "correctness",
    severity: str = "MEDIUM",
    description: str = "Example finding.",
) -> Finding:
    return Finding(
        id=finding_id,
        category=category,
        severity=severity,
        description=description,
    )


def make_evaluator_output(
    findings: list[Finding],
) -> EvaluatorOutput:
    return EvaluatorOutput(
        final_decision="pass_with_warnings",
        rule_score=0.0,
        execution_score=0.0,
        security_score=0.9,
        maintainability_score=0.9,
        correctness_score=0.9,
        findings=findings,
    )


def test_evaluator_combined_findings_are_flattened():
    review_finding = make_finding(
        "review_1",
        category="correctness",
        description="Missing validation.",
    )
    security_finding = make_finding(
        "security_1",
        category="security",
        severity="HIGH",
        description="Path traversal risk.",
    )

    result = EvaluatorAgent._normalize_findings(
        result=make_evaluator_output(
            [
                review_finding.model_copy(update={"status": "resolved"}),
                security_finding.model_copy(update={"status": "unresolved"}),
            ]
        ),
        original_findings=[
            review_finding,
            security_finding,
        ],
    )

    assert [finding.id for finding in result.findings] == [
        "review_1",
        "security_1",
    ]


def test_evaluator_can_mark_finding_resolved():
    original = make_finding(
        "finding_1",
        description="Missing validation.",
    )

    evaluated = original.model_copy(update={"status": "resolved"})

    result = EvaluatorAgent._normalize_findings(
        result=make_evaluator_output([evaluated]),
        original_findings=[original],
    )

    assert result.findings[0].id == "finding_1"
    assert result.findings[0].description == "Missing validation."
    assert result.findings[0].status == "resolved"


def test_evaluator_can_leave_finding_unresolved():
    original = make_finding(
        "finding_1",
        description="Missing validation.",
    )

    evaluated = original.model_copy(update={"status": "unresolved"})

    result = EvaluatorAgent._normalize_findings(
        result=make_evaluator_output([evaluated]),
        original_findings=[original],
    )

    assert result.findings[0].status == "unresolved"


def test_missing_evaluator_finding_remains_unresolved():
    original = make_finding(
        "finding_1",
        description="Missing validation.",
    )

    result = EvaluatorAgent._normalize_findings(
        result=make_evaluator_output([]),
        original_findings=[original],
    )

    assert len(result.findings) == 1
    assert result.findings[0].id == "finding_1"
    assert result.findings[0].status == "unresolved"


def test_evaluator_cannot_introduce_arbitrary_findings():
    original = make_finding(
        "finding_1",
        description="Missing validation.",
    )
    invented = make_finding(
        "invented_finding",
        category="security",
        severity="CRITICAL",
        description="Invented vulnerability.",
    )

    result = EvaluatorAgent._normalize_findings(
        result=make_evaluator_output(
            [
                original.model_copy(update={"status": "resolved"}),
                invented,
            ]
        ),
        original_findings=[original],
    )

    assert [finding.id for finding in result.findings] == ["finding_1"]
    assert result.findings[0].status == "resolved"


def test_evaluator_preserves_original_finding_metadata():
    original = make_finding(
        "finding_1",
        category="security",
        severity="HIGH",
        description="Original security finding.",
    )

    evaluated = Finding(
        id="finding_1",
        category="incorrect_category",
        severity="LOW",
        description="Changed description.",
        status="resolved",
    )

    result = EvaluatorAgent._normalize_findings(
        result=make_evaluator_output([evaluated]),
        original_findings=[original],
    )

    finding = result.findings[0]

    assert finding.id == "finding_1"
    assert finding.category == "security"
    assert finding.severity == "HIGH"
    assert finding.description == "Original security finding."
    assert finding.status == "resolved"
