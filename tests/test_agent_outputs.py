from apps.schemas.agent_outputs import Finding, ReviewerOutput, SecurityAuditOutput


def test_finding_defaults_to_unresolved():
    finding = Finding(
        id="finding_1",
        category="correctness",
        severity="MEDIUM",
        description="Missing input validation.",
    )

    assert finding.status == "unresolved"


def test_finding_accepts_resolved_status():
    finding = Finding(
        id="finding_1",
        category="correctness",
        severity="MEDIUM",
        description="Missing input validation.",
        status="resolved",
    )

    assert finding.status == "resolved"


def test_security_audit_aggregate_properties_use_unresolved_findings():
    audit = SecurityAuditOutput(
        findings=[
            Finding(
                id="finding_low",
                category="security",
                severity="LOW",
                description="Minor issue.",
                status="resolved",
            ),
            Finding(
                id="finding_high",
                category="security",
                severity="HIGH",
                description="Path traversal risk.",
            ),
        ]
    )

    assert audit.status == "FAILED"
    assert audit.severity == "HIGH"
    assert audit.vulnerabilities == ["Path traversal risk."]


def test_security_audit_is_passed_when_all_findings_are_resolved():
    audit = SecurityAuditOutput(
        findings=[
            Finding(
                id="finding_1",
                category="security",
                severity="CRITICAL",
                description="Previously unsafe operation.",
                status="resolved",
            )
        ]
    )

    assert audit.status == "PASSED"
    assert audit.severity == "NONE"
    assert audit.vulnerabilities == []


def test_reviewer_issues_property_is_derived_from_findings():
    review = ReviewerOutput(
        summary="Two issues found.",
        findings=[
            Finding(
                id="finding_1",
                category="correctness",
                severity="MEDIUM",
                description="Missing validation.",
            ),
            Finding(
                id="finding_2",
                category="maintainability",
                severity="LOW",
                description="Function is too large.",
            ),
        ],
    )

    assert review.issues == [
        "Missing validation.",
        "Function is too large.",
    ]
