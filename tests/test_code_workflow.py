"""Tests for CodeWorkflow PR-context propagation and persistence."""

from unittest.mock import AsyncMock, Mock

import pytest

from apps.agents.code_writer_agent import CodeWriterAgent
from apps.agents.evaluator_agent import EvaluatorAgent
from apps.agents.inspection_agent import InspectionAgent
from apps.agents.planner_agent import PlannerAgent
from apps.agents.test_generator_agent import TestGeneratorAgent
from apps.core.constants import DEFAULT_MAX_ROUNDS
from apps.core.workflow_config import WorkflowConfig
from apps.database.session import close_database_engine
from apps.integrations.github.models import GitHubChangedFile
from apps.repositories.unit_of_work import UnitOfWork
from apps.schemas.agent_outputs import (
    CodeWriterOutput,
    EvaluatorOutput,
    PlannerOutput,
    ReviewerOutput,
    SecurityAuditOutput,
    TestGeneratorOutput,
)
from apps.schemas.requests import ReviewRequest
from apps.schemas.review_context import PRContext
from apps.tools.test_runner import TestRunResult
from apps.workflows.code_workflow import CodeWorkflow


@pytest.fixture
def workflow_config() -> WorkflowConfig:
    return WorkflowConfig(
        max_rounds=DEFAULT_MAX_ROUNDS,
        force_retry_rounds=0,
        always_retry=False,
    )


@pytest.fixture
def review_context() -> PRContext:
    return PRContext(
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


@pytest.fixture
def review_request(review_context: PRContext) -> ReviewRequest:
    return ReviewRequest(
        instruction="Review and improve this function.",
        code="""\
def add(a: int, b: int) -> int:
    return a + b
""",
        review_context=review_context,
        save_artifacts=False,
    )


@pytest.fixture
def planner_output() -> PlannerOutput:
    return PlannerOutput(
        task_type="review_refactor",
        requires_generation=False,
        requires_refactor=True,
        requires_tests=True,
    )


@pytest.fixture
def reviewer_output() -> ReviewerOutput:
    return ReviewerOutput(
        summary="No significant issues found.",
        findings=[],
        suggestions=[],
        risk_level="LOW",
    )


@pytest.fixture
def security_output() -> SecurityAuditOutput:
    return SecurityAuditOutput(
        findings=[],
        notes=None,
    )


@pytest.fixture
def code_writer_output() -> CodeWriterOutput:
    return CodeWriterOutput(
        code="""\
def add(a: int, b: int) -> int:
    return a + b
""",
        explanation="No changes required.",
        changed_behavior_warnings=[],
    )


@pytest.fixture
def test_generator_output() -> TestGeneratorOutput:
    return TestGeneratorOutput(
        tests="""\
from solution import add


def test_add():
    assert add(1, 2) == 3
""",
        coverage_notes=[],
    )


@pytest.fixture
def test_run_result() -> TestRunResult:
    return TestRunResult(
        status="passed",
        exit_code=0,
        duration_ms=10,
        stdout="1 passed",
        stderr="",
        tests_total=1,
        tests_passed=1,
        tests_failed=0,
        tests_skipped=0,
        tests_xfailed=0,
        tests_xpassed=0,
        tests=[],
    )


@pytest.fixture
def evaluator_output() -> EvaluatorOutput:
    return EvaluatorOutput(
        final_decision="pass",
        rule_score=1.0,
        execution_score=1.0,
        llm_score=1.0,
        security_score=1.0,
        maintainability_score=1.0,
        correctness_score=1.0,
        final_score=1.0,
        findings=[],
        reasons=[],
        retry_feedback=None,
    )


@pytest.fixture
async def cleanup_database_engine():
    yield
    await close_database_engine()


def create_workflow(
    workflow_config: WorkflowConfig,
    *,
    planner: PlannerAgent | None = None,
    code_writer: CodeWriterAgent | None = None,
    inspector: InspectionAgent | None = None,
    test_generator: TestGeneratorAgent | None = None,
    evaluator: EvaluatorAgent | None = None,
) -> CodeWorkflow:
    return CodeWorkflow(
        planner=planner or Mock(spec=PlannerAgent),
        code_writer=code_writer or Mock(spec=CodeWriterAgent),
        inspector=inspector or Mock(spec=InspectionAgent),
        test_generator=test_generator or Mock(spec=TestGeneratorAgent),
        evaluator=evaluator or Mock(spec=EvaluatorAgent),
        config=workflow_config,
    )


@pytest.mark.anyio
async def test_code_workflow_passes_and_persists_review_context_for_inspection(
    cleanup_database_engine,
    workflow_config: WorkflowConfig,
    review_context: PRContext,
    review_request: ReviewRequest,
    planner_output: PlannerOutput,
    reviewer_output: ReviewerOutput,
    security_output: SecurityAuditOutput,
    code_writer_output: CodeWriterOutput,
    test_generator_output: TestGeneratorOutput,
    test_run_result: TestRunResult,
    evaluator_output: EvaluatorOutput,
    monkeypatch: pytest.MonkeyPatch,
):
    planner = Mock(spec=PlannerAgent)
    planner.run = AsyncMock(return_value=(planner_output, 5))

    inspector = Mock(spec=InspectionAgent)
    inspector.run = AsyncMock(
        side_effect=[
            (reviewer_output, 5),
            (security_output, 5),
        ]
    )

    code_writer = Mock(spec=CodeWriterAgent)
    code_writer.run = AsyncMock(return_value=(code_writer_output, 5))

    test_generator = Mock(spec=TestGeneratorAgent)
    test_generator.run = AsyncMock(return_value=(test_generator_output, 5))

    evaluator = Mock(spec=EvaluatorAgent)
    evaluator.run = AsyncMock(return_value=(evaluator_output, 5))

    workflow = create_workflow(
        workflow_config,
        planner=planner,
        inspector=inspector,
        code_writer=code_writer,
        test_generator=test_generator,
        evaluator=evaluator,
    )

    monkeypatch.setattr(
        "apps.workflows.code_workflow.run_pytest_for_code",
        AsyncMock(return_value=test_run_result),
    )

    result = await workflow.run(review_request)

    # Verify CodeWorkflow passes the same PR context to both inspection modes.
    reviewer_call = inspector.run.await_args_list[0]
    assert reviewer_call.kwargs["mode"] == "reviewer"
    assert reviewer_call.kwargs["review_context"] == review_context

    security_call = inspector.run.await_args_list[1]
    assert security_call.kwargs["mode"] == "security_auditor"
    assert security_call.kwargs["review_context"] == review_context

    # Verify both inspection steps completed successfully.
    reviewer_trace = next(
        step for step in result.steps if step.step_name == "inspection.reviewer"
    )
    security_trace = next(
        step for step in result.steps if step.step_name == "inspection.security_auditor"
    )

    assert reviewer_trace.status == "success"
    assert security_trace.status == "success"

    # Verify CodeWorkflow persists review_context in AgentStep
    async with UnitOfWork() as uow:
        persisted_steps = await uow.agent_steps.list_by_workflow(result.workflow_run_id)

    persisted_reviewer = next(
        step for step in persisted_steps if step.agent_name == "inspection.reviewer"
    )
    persisted_security = next(
        step
        for step in persisted_steps
        if step.agent_name == "inspection.security_auditor"
    )

    expected_context = review_context.model_dump(mode="json")

    assert persisted_reviewer.input_json["review_context"] == expected_context
    assert persisted_security.input_json["review_context"] == expected_context
