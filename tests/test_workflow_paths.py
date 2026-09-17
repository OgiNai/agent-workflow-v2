"""Tests for deterministic workflow execution paths."""

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


@pytest.fixture(autouse=True)
async def cleanup_database_engine() -> None:
    yield
    await close_database_engine()


@pytest.fixture
def workflow_config() -> WorkflowConfig:
    return WorkflowConfig(
        max_rounds=DEFAULT_MAX_ROUNDS,
        force_retry_rounds=0,
        always_retry=False,
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


@pytest.mark.anyio
async def test_generate_workflow_calls_code_writer_in_generate_then_refactor_mode(
    workflow_config: WorkflowConfig,
    test_run_result: TestRunResult,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    planner = Mock(spec=PlannerAgent)
    planner.run = AsyncMock(
        return_value=(
            PlannerOutput(
                task_type="generate",
                requires_generation=True,
                requires_refactor=True,
                requires_tests=True,
            ),
            5,
        )
    )

    code_writer = Mock(spec=CodeWriterAgent)
    code_writer.run = AsyncMock(
        side_effect=[
            (
                CodeWriterOutput(
                    code="def generated():\n    return 1\n",
                    explanation="Generated implementation.",
                    changed_behavior_warnings=[],
                ),
                5,
            ),
            (
                CodeWriterOutput(
                    code="def generated():\n    return 1\n",
                    explanation="No changes required.",
                    changed_behavior_warnings=[],
                ),
                5,
            ),
        ]
    )

    inspector = Mock(spec=InspectionAgent)
    inspector.run = AsyncMock(
        side_effect=[
            (
                ReviewerOutput(
                    summary="No issues.",
                    findings=[],
                    suggestions=[],
                    risk_level="LOW",
                ),
                5,
            ),
            (
                SecurityAuditOutput(
                    findings=[],
                    notes=None,
                ),
                5,
            ),
        ]
    )

    test_generator = Mock(spec=TestGeneratorAgent)
    test_generator.run = AsyncMock(
        return_value=(
            TestGeneratorOutput(
                tests=(
                    "from solution import generated\n\n"
                    "def test_generated():\n"
                    "    assert generated() == 1\n"
                ),
                coverage_notes=[],
            ),
            5,
        )
    )

    evaluator = Mock(spec=EvaluatorAgent)
    evaluator.run = AsyncMock(
        return_value=(
            EvaluatorOutput(
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
            ),
            5,
        )
    )

    test_runner = AsyncMock(return_value=test_run_result)

    monkeypatch.setattr(
        "apps.workflows.code_workflow.run_pytest_for_code",
        test_runner,
    )

    workflow = CodeWorkflow(
        planner=planner,
        code_writer=code_writer,
        inspector=inspector,
        test_generator=test_generator,
        evaluator=evaluator,
        config=workflow_config,
    )

    request = ReviewRequest(
        task_type="generate",
        instruction="Create a function that returns one.",
        save_artifacts=False,
    )

    result = await workflow.run(request)

    assert result.status == "completed"
    assert result.final_decision == "pass"

    assert code_writer.run.await_count == 2

    generate_call = code_writer.run.await_args_list[0]
    refactor_call = code_writer.run.await_args_list[1]

    assert generate_call.kwargs["mode"] == "generate"
    assert generate_call.kwargs["instruction"] == request.instruction
    assert generate_call.kwargs["code"] is None

    assert refactor_call.kwargs["mode"] == "refactor"
    assert refactor_call.kwargs["code"] == "def generated():\n    return 1\n"

    step_names = [step.step_name for step in result.steps]

    assert step_names.index("code_writer.generate") < step_names.index(
        "inspection.reviewer"
    )
    assert step_names.index("inspection.reviewer") < step_names.index(
        "inspection.security_auditor"
    )
    assert step_names.index("inspection.security_auditor") < step_names.index(
        "code_writer.refactor"
    )
    assert step_names.index("code_writer.refactor") < step_names.index("test_generator")
    assert step_names.index("test_generator") < step_names.index("test_runner")
    assert step_names.index("test_runner") < step_names.index("evaluator")
