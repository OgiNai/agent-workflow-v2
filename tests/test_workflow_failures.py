"""Tests for workflow failure handling and resilience."""

import logging
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
from apps.database.unit_of_work import UnitOfWork
from apps.llm.llm_exceptions import LLMGenerationError
from apps.schemas.agent_outputs import (
    CodeWriterOutput,
    EvaluatorOutput,
    PlannerOutput,
    ReviewerOutput,
    SecurityAuditOutput,
    TestGeneratorOutput,
)
from apps.schemas.requests import ReviewRequest
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
def review_request() -> ReviewRequest:
    return ReviewRequest(
        instruction="Review and improve this function.",
        code="""
def add(a: int, b: int) -> int:
    return a + b
""",
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
        code="""
def add(a: int, b: int) -> int:
    return a + b
""",
        explanation="No changes required.",
        changed_behavior_warnings=[],
    )


@pytest.fixture
def test_generator_output() -> TestGeneratorOutput:
    return TestGeneratorOutput(
        tests="""
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
async def test_llm_failure_marks_workflow_failed(
    cleanup_database_engine,
    workflow_config: WorkflowConfig,
    review_request: ReviewRequest,
):
    internal_error = "Gemini provider failure: https://internal.example/api key=secret"
    planner = Mock(spec=PlannerAgent)
    planner.run = AsyncMock(side_effect=LLMGenerationError(internal_error))

    workflow = create_workflow(
        workflow_config,
        planner=planner,
    )

    result = await workflow.run(review_request)

    assert result.status == "failed"
    assert result.final_decision == "failed"
    assert result.summary == "Workflow execution failed."

    workflow_steps = [step for step in result.steps if step.step_name == "planner"]
    assert len(workflow_steps) == 1
    assert workflow_steps[0].status == "failed"

    planner_step = next(step for step in result.steps if step.step_name == "planner")
    assert planner_step.status == "failed"
    assert planner_step.detail == "Agent execution failed."


@pytest.mark.anyio
async def test_unexpected_agent_failure_marks_workflow_failed(
    cleanup_database_engine,
    workflow_config: WorkflowConfig,
    review_request: ReviewRequest,
    planner_output: PlannerOutput,
    caplog: pytest.LogCaptureFixture,
):
    planner = Mock(spec=PlannerAgent)
    planner.run = AsyncMock(return_value=(planner_output, 5))

    internal_error = "unexpected reviewer failure: /srv/private/project/.env"
    inspector = Mock(spec=InspectionAgent)
    inspector.run = AsyncMock(side_effect=RuntimeError(internal_error))

    workflow = create_workflow(
        workflow_config,
        planner=planner,
        inspector=inspector,
    )

    with caplog.at_level(logging.ERROR, logger="apps.workflows.code_workflow"):
        result = await workflow.run(review_request)

    assert "agent_execution_failed" in caplog.text
    assert "unexpected reviewer failure: /srv/private/project/.env" in caplog.text

    assert result.status == "failed"
    assert result.final_decision == "failed"
    assert result.summary == "Workflow execution failed."

    reviewer_steps = [
        step for step in result.steps if step.step_name == "inspection.reviewer"
    ]
    assert len(reviewer_steps) == 1
    assert reviewer_steps[0].status == "failed"
    assert reviewer_steps[0].detail == "Agent execution failed."


@pytest.mark.anyio
async def test_test_runner_failure_marks_workflow_failed(
    cleanup_database_engine,
    workflow_config: WorkflowConfig,
    review_request: ReviewRequest,
    planner_output: PlannerOutput,
    reviewer_output: ReviewerOutput,
    security_output: SecurityAuditOutput,
    code_writer_output: CodeWriterOutput,
    test_generator_output: TestGeneratorOutput,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
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

    workflow = create_workflow(
        workflow_config,
        planner=planner,
        inspector=inspector,
        code_writer=code_writer,
        test_generator=test_generator,
    )

    internal_error = "pytest infrastructure failure: /tmp/secret-test-workspace"
    test_runner = AsyncMock(side_effect=RuntimeError(internal_error))

    monkeypatch.setattr(
        "apps.workflows.code_workflow.run_pytest_for_code",
        test_runner,
    )

    with caplog.at_level(logging.ERROR, logger="apps.workflows.code_workflow"):
        result = await workflow.run(review_request)

    assert "test_runner_execution_failed" in caplog.text
    assert "pytest infrastructure failure: /tmp/secret-test-workspace" in caplog.text

    assert result.status == "failed"
    assert result.final_decision == "failed"
    assert result.summary == "Workflow execution failed."

    test_runner_steps = [
        step for step in result.steps if step.step_name == "test_runner"
    ]

    assert len(test_runner_steps) == 1
    assert test_runner_steps[0].status == "failed"
    assert test_runner_steps[0].detail == "Test runner execution failed."


@pytest.mark.anyio
async def test_failed_workflow_preserves_completed_agent_steps(
    cleanup_database_engine,
    workflow_config: WorkflowConfig,
    review_request: ReviewRequest,
    planner_output: PlannerOutput,
):
    planner = Mock(spec=PlannerAgent)
    planner.run = AsyncMock(return_value=(planner_output, 5))

    inspector = Mock(spec=InspectionAgent)
    inspector.run = AsyncMock(side_effect=RuntimeError("security audit unavailable"))

    workflow = create_workflow(
        workflow_config,
        planner=planner,
        inspector=inspector,
    )

    result = await workflow.run(review_request)

    assert result.status == "failed"

    step_names = [step.step_name for step in result.steps]

    assert "input_router" in step_names
    assert "planner" in step_names
    assert "inspection.reviewer" in step_names
    assert "workflow" in step_names

    planner_steps = [step for step in result.steps if step.step_name == "planner"]

    assert planner_steps[0].status == "success"

    reviewer_steps = [
        step for step in result.steps if step.step_name == "inspection.reviewer"
    ]

    assert reviewer_steps[0].status == "failed"


@pytest.mark.anyio
async def test_successful_workflow_still_returns_completed(
    cleanup_database_engine,
    workflow_config: WorkflowConfig,
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

    assert result.status == "completed"
    assert result.final_decision == "pass"
    assert result.summary == "Workflow completed successfully."
    assert result.rounds_executed == 1

    assert all(step.status != "failed" for step in result.steps)


@pytest.mark.anyio
async def test_failed_workflow_is_persisted_with_sanitized_summary(
    cleanup_database_engine,
    workflow_config: WorkflowConfig,
    review_request: ReviewRequest,
    planner_output: PlannerOutput,
):
    planner = Mock(spec=PlannerAgent)
    planner.run = AsyncMock(return_value=(planner_output, 5))

    internal_error = "database failure: postgresql://user:secret@internal-db:5432/app"
    inspector = Mock(spec=InspectionAgent)
    inspector.run = AsyncMock(side_effect=RuntimeError(internal_error))

    workflow = create_workflow(
        workflow_config,
        planner=planner,
        inspector=inspector,
    )

    result = await workflow.run(review_request)

    assert result.status == "failed"
    assert result.final_decision == "failed"
    assert result.summary == "Workflow execution failed."

    async with UnitOfWork() as uow:
        persisted_workflow = await uow.workflows.get(result.workflow_run_id)

    assert persisted_workflow is not None
    assert persisted_workflow.status == "failed"
    assert persisted_workflow.final_decision == "failed"
    assert persisted_workflow.summary == "Workflow execution failed."


@pytest.mark.anyio
async def test_failure_during_retry_preserves_previous_round_steps(
    cleanup_database_engine,
    workflow_config: WorkflowConfig,
    review_request: ReviewRequest,
    planner_output: PlannerOutput,
    reviewer_output: ReviewerOutput,
    security_output: SecurityAuditOutput,
    code_writer_output: CodeWriterOutput,
    test_generator_output: TestGeneratorOutput,
    test_run_result: TestRunResult,
    monkeypatch: pytest.MonkeyPatch,
):
    planner = Mock(spec=PlannerAgent)
    planner.run = AsyncMock(return_value=(planner_output, 5))

    inspector = Mock(spec=InspectionAgent)
    inspector.run = AsyncMock(
        side_effect=[
            (reviewer_output, 5),
            (security_output, 5),
            (reviewer_output, 5),
            RuntimeError("security audit unavailable during retry"),
        ]
    )

    code_writer = Mock(spec=CodeWriterAgent)
    code_writer.run = AsyncMock(return_value=(code_writer_output, 5))

    test_generator = Mock(spec=TestGeneratorAgent)
    test_generator.run = AsyncMock(return_value=(test_generator_output, 5))

    retry_evaluation = EvaluatorOutput(
        final_decision="retry",
        rule_score=0.5,
        execution_score=1.0,
        llm_score=0.5,
        security_score=0.5,
        maintainability_score=0.5,
        correctness_score=0.5,
        final_score=0.5,
        findings=[],
        reasons=["Retry required."],
        retry_feedback="Further improvements are required.",
    )

    evaluator = Mock(spec=EvaluatorAgent)
    evaluator.run = AsyncMock(return_value=(retry_evaluation, 5))

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

    assert result.status == "failed"
    assert result.final_decision == "failed"
    assert result.summary == "Workflow execution failed."
    assert result.rounds_executed == 2

    step_names = [step.step_name for step in result.steps]

    # Initial workflow and planner execution are preserved.
    assert "input_router" in step_names
    assert "planner" in step_names

    # Round 1 completed successfully before the retry.
    round_one_steps = [step for step in result.steps if step.round_number == 1]

    assert [step.step_name for step in round_one_steps] == [
        "inspection.reviewer",
        "inspection.security_auditor",
        "code_writer.refactor",
        "test_generator",
        "test_runner",
        "evaluator",
        "retry_policy",
    ]

    assert all(step.status == "success" for step in round_one_steps)

    # Round 2 reached the reviewer successfully.
    round_two_reviewer = [
        step
        for step in result.steps
        if step.round_number == 2 and step.step_name == "inspection.reviewer"
    ]

    assert len(round_two_reviewer) == 1
    assert round_two_reviewer[0].status == "success"

    # Round 2 failed at the security auditor.
    round_two_security = [
        step
        for step in result.steps
        if step.round_number == 2 and step.step_name == "inspection.security_auditor"
    ]

    assert len(round_two_security) == 1
    assert round_two_security[0].status == "failed"
    assert round_two_security[0].detail == "Agent execution failed."

    # The workflow-level failure is also preserved.
    workflow_steps = [step for step in result.steps if step.step_name == "workflow"]

    assert len(workflow_steps) == 1
    assert workflow_steps[0].status == "failed"
    assert workflow_steps[0].detail == "Workflow execution failed."

    # The failed round must not execute downstream agents.
    assert code_writer.run.await_count == 1
    assert test_generator.run.await_count == 1
    assert evaluator.run.await_count == 1
