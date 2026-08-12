"""Unified code generation/review/refactoring workflow."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from functools import partial
from time import perf_counter
from typing import Any, TypeVar
from uuid import uuid4

from pydantic import BaseModel

from apps.agents.code_writer_agent import CodeWriterAgent
from apps.agents.evaluator_agent import EvaluatorAgent
from apps.agents.inspection_agent import InspectionAgent
from apps.agents.planner_agent import PlannerAgent
from apps.agents.test_generator_agent import TestGeneratorAgent
from apps.core.settings import get_workflow_settings
from apps.core.workflow_config import WorkflowConfig
from apps.database.models import AgentStep, Artifact, WorkflowRun
from apps.database.unit_of_work import UnitOfWork
from apps.evals.execution_eval import calculate_execution_score
from apps.evals.rule_based import calculate_rule_score
from apps.schemas.agent_outputs import EvaluatorOutput
from apps.schemas.requests import ReviewRequest
from apps.schemas.responses import ReviewResponse
from apps.schemas.workflow import (
    CandidateCode,
    RouterResult,
    WorkflowContext,
    WorkflowStepTrace,
)
from apps.tools.test_runner import TestRunResult, run_pytest_for_code
from apps.workflows.artifact_manager import save_artifact
from apps.workflows.input_router import route_input

# from apps.workflows.retry_policy import should_retry

logger = logging.getLogger(__name__)

AgentResultT = TypeVar("AgentResultT", bound=BaseModel)


class CodeWorkflow:
    """Orchestrates the unified workflow for both feature requests and code review requests."""

    def __init__(
        self,
        *,
        planner: PlannerAgent | None = None,
        code_writer: CodeWriterAgent | None = None,
        inspector: InspectionAgent | None = None,
        test_generator: TestGeneratorAgent | None = None,
        evaluator: EvaluatorAgent | None = None,
        config: WorkflowConfig | None = None,
    ) -> None:
        self.planner = planner or PlannerAgent()
        self.code_writer = code_writer or CodeWriterAgent()
        self.inspector = inspector or InspectionAgent()
        self.test_generator = test_generator or TestGeneratorAgent()
        self.evaluator = evaluator or EvaluatorAgent()
        self._workflow_config = config or WorkflowConfig(
            max_rounds=1,
            force_retry_rounds=0,
            always_retry=False,
        )

    async def run(self, request: ReviewRequest) -> ReviewResponse:
        workflow_run_id = uuid4()
        workflow_started_at = perf_counter()

        context = WorkflowContext(
            workflow_run_id=workflow_run_id,
            request_id=str(workflow_run_id),
        )

        rounds_executed = 0
        step_order = 1
        final_evaluation: EvaluatorOutput | None = None
        final_code: str | None = None
        passing_decisions = {"pass", "pass_with_warnings"}
        retry_override_active = False

        initial_source_type = (
            "inline_code"
            if request.code
            else "file_path"
            if request.file_path
            else "none"
        )

        workflow = WorkflowRun(
            id=workflow_run_id,
            instruction=request.instruction,
            source_type=initial_source_type,
            task_type=request.task_type,
            status="running",
            retry_count=0,
        )

        async with UnitOfWork() as uow:
            await uow.workflows.create(workflow)

            try:
                router_result = route_input(request)

                workflow.source_type = router_result.source_type
                workflow.task_type = router_result.task_type
                await uow.workflows.update(workflow)

                context.traces.append(
                    WorkflowStepTrace(
                        step_name="input_router",
                        step_type="workflow",
                        status="success",
                        detail=(
                            f"Resolved {router_result.source_type} "
                            f"-> {router_result.task_type}"
                        ),
                    )
                )

                plan = await self._run_agent(
                    context=context,
                    uow=uow,
                    step_name="planner",
                    step_order=step_order,
                    round_number=0,
                    input_data={
                        "instruction": router_result.instruction,
                        "task_type": router_result.task_type,
                        "max_rounds": self._workflow_config.max_rounds,
                    },
                    runner=partial(
                        self.planner.run,
                        router_result,
                        self._workflow_config.max_rounds,
                    ),
                )
                step_order += 1

                candidate = await self._create_initial_candidate(
                    request=request,
                    router_result=router_result,
                    requires_generation=plan.requires_generation,
                    context=context,
                    uow=uow,
                    step_order=step_order,
                )

                if plan.requires_generation:
                    step_order += 1

                previous_evaluation: EvaluatorOutput | None = None

                for round_number in range(
                    1,
                    self._workflow_config.max_rounds + 1,
                ):
                    rounds_executed = round_number

                    review = await self._run_agent(
                        context=context,
                        uow=uow,
                        step_name="inspection.reviewer",
                        step_order=step_order,
                        round_number=round_number,
                        input_data={
                            "instruction": router_result.instruction,
                            "code": candidate.code,
                        },
                        runner=partial(
                            self.inspector.run,
                            mode="reviewer",
                            instruction=router_result.instruction,
                            code=candidate.code,
                        ),
                    )
                    step_order += 1

                    security = await self._run_agent(
                        context=context,
                        uow=uow,
                        step_name="inspection.security_auditor",
                        step_order=step_order,
                        round_number=round_number,
                        input_data={
                            "instruction": router_result.instruction,
                            "code": candidate.code,
                        },
                        runner=partial(
                            self.inspector.run,
                            mode="security_auditor",
                            instruction=router_result.instruction,
                            code=candidate.code,
                        ),
                    )
                    step_order += 1

                    writer_mode = "refactor" if round_number == 1 else "repair"

                    writer_output = await self._run_agent(
                        context=context,
                        uow=uow,
                        step_name=f"code_writer.{writer_mode}",
                        step_order=step_order,
                        round_number=round_number,
                        input_data={
                            "instruction": router_result.instruction,
                            "code": candidate.code,
                            "review": review.model_dump(mode="json"),
                            "security": security.model_dump(mode="json"),
                            "evaluation": (
                                previous_evaluation.model_dump(mode="json")
                                if previous_evaluation is not None
                                else None
                            ),
                        },
                        runner=partial(
                            self.code_writer.run,
                            mode=writer_mode,
                            instruction=router_result.instruction,
                            code=candidate.code,
                            review=review,
                            security=security,
                            evaluation=previous_evaluation,
                        ),
                        exclude={"code"},
                    )
                    step_order += 1

                    candidate = CandidateCode(
                        code=writer_output.code,
                        origin=f"code_writer.{writer_mode}",
                        round_number=round_number,
                    )
                    final_code = candidate.code

                    tests_output = await self._run_agent(
                        context=context,
                        uow=uow,
                        step_name="test_generator",
                        step_order=step_order,
                        round_number=round_number,
                        input_data={
                            "instruction": router_result.instruction,
                            "code": candidate.code,
                        },
                        runner=partial(
                            self.test_generator.run,
                            instruction=router_result.instruction,
                            code=candidate.code,
                        ),
                        exclude={"tests"},
                    )
                    step_order += 1

                    test_started_at = perf_counter()

                    try:
                        test_result = await run_pytest_for_code(
                            candidate.code,
                            tests_output.tests,
                        )
                    except Exception as exc:
                        test_duration_ms = int(
                            (perf_counter() - test_started_at) * 1000
                        )

                        context.traces.append(
                            WorkflowStepTrace(
                                step_name="test_runner",
                                step_type="tool",
                                status="failed",
                                latency_ms=test_duration_ms,
                                round_number=round_number,
                                detail=str(exc),
                            )
                        )
                        raise

                    context.traces.append(
                        WorkflowStepTrace(
                            step_name="test_runner",
                            step_type="tool",
                            status=(
                                "success"
                                if test_result.status == "passed"
                                else "failed"
                            ),
                            latency_ms=test_result.duration_ms,
                            round_number=round_number,
                            metadata=test_result.model_dump(mode="json"),
                        )
                    )

                    rule_score, rule_notes = calculate_rule_score(
                        candidate.code,
                        security,
                    )
                    execution_score = calculate_execution_score(test_result)

                    evaluation = await self._run_agent(
                        context=context,
                        uow=uow,
                        step_name="evaluator",
                        step_order=step_order,
                        round_number=round_number,
                        input_data={
                            "instruction": router_result.instruction,
                            "code": candidate.code,
                            "review": review.model_dump(mode="json"),
                            "security": security.model_dump(mode="json"),
                            "test_result": test_result.model_dump(mode="json"),
                            "rule_score": rule_score,
                            "execution_score": execution_score,
                        },
                        runner=partial(
                            self.evaluator.run,
                            instruction=router_result.instruction,
                            code=candidate.code,
                            review=review,
                            security=security,
                            test_result=test_result,
                            rule_score=rule_score,
                            execution_score=execution_score,
                            round_number=round_number,
                        ),
                    )
                    step_order += 1

                    evaluation.reasons.extend(rule_notes)

                    final_evaluation = evaluation
                    previous_evaluation = evaluation

                    if request.save_artifacts:
                        await self._save_round_artifacts(
                            context=context,
                            uow=uow,
                            round_number=round_number,
                            candidate_code=candidate.code,
                            tests=tests_output.tests,
                            test_result=test_result,
                            evaluation=evaluation,
                        )

                    retry_override_active = self._workflow_config.always_retry or (
                        self._workflow_config.force_retry_rounds > 0
                        and round_number < self._workflow_config.force_retry_rounds
                    )

                    evaluator_decision = evaluation.final_decision
                    workflow_decision = evaluator_decision

                    if retry_override_active:
                        workflow_decision = "retry"

                        context.traces.append(
                            WorkflowStepTrace(
                                step_name="debug_retry_override",
                                step_type="workflow",
                                status="success",
                                round_number=round_number,
                                detail=("Retry forced by workflow configuration."),
                                metadata={
                                    "evaluator_decision": evaluator_decision,
                                    "workflow_decision": workflow_decision,
                                    "override_reason": (
                                        "always_retry"
                                        if self._workflow_config.always_retry
                                        else "force_retry_rounds"
                                    ),
                                },
                            )
                        )

                    if workflow_decision in passing_decisions:
                        break

                    context.traces.append(
                        WorkflowStepTrace(
                            step_name="retry_policy",
                            step_type="workflow",
                            status="success",
                            round_number=round_number,
                            detail=(
                                "Retry routes back to Reviewer with "
                                "latest candidate code."
                            ),
                        )
                    )

                if final_evaluation is None:
                    raise RuntimeError(
                        "Workflow completed without an evaluation result."
                    )

                final_decision = (
                    final_evaluation.final_decision
                    if final_evaluation.final_decision in passing_decisions
                    else "unresolved"
                )

                status = (
                    "completed"
                    if final_decision in passing_decisions
                    else "completed_with_warnings"
                )

                if final_decision in passing_decisions:
                    final_summary = "Workflow completed successfully."
                else:
                    final_summary = "Workflow completed without passing evaluation."

                if retry_override_active:
                    test_for = (
                        "always retry"
                        if self._workflow_config.always_retry
                        else "force rounds"
                    )
                    final_summary += (
                        f" Workflow ran in debug mode, tested for {test_for}."
                    )

                workflow.status = status
                workflow.final_decision = final_decision
                workflow.summary = final_summary
                workflow.retry_count = max(rounds_executed - 1, 0)
                workflow.duration_ms = int(
                    (perf_counter() - workflow_started_at) * 1000
                )

                workflow.rule_score = final_evaluation.rule_score
                workflow.execution_score = final_evaluation.execution_score
                workflow.llm_score = final_evaluation.llm_score
                workflow.security_score = final_evaluation.security_score
                workflow.maintainability_score = final_evaluation.maintainability_score
                workflow.correctness_score = final_evaluation.correctness_score
                workflow.overall_score = final_evaluation.final_score

                await uow.workflows.update(workflow)

                return ReviewResponse(
                    workflow_run_id=workflow_run_id,
                    status=status,
                    task_type=router_result.task_type,
                    source_type=router_result.source_type,
                    final_decision=final_decision,
                    summary=final_summary,
                    final_code=final_code,
                    evaluation=final_evaluation,
                    artifacts=context.artifacts,
                    rounds_executed=rounds_executed,
                    steps=context.traces,
                )

            except Exception as exc:
                logger.exception("workflow_failed")

                workflow.status = "failed"
                workflow.final_decision = "failed"
                workflow.summary = f"Workflow failed: {exc}"
                workflow.retry_count = max(rounds_executed - 1, 0)
                workflow.duration_ms = int(
                    (perf_counter() - workflow_started_at) * 1000
                )

                context.traces.append(
                    WorkflowStepTrace(
                        step_name="workflow",
                        step_type="workflow",
                        status="failed",
                        detail=str(exc),
                    )
                )

                await uow.workflows.update(workflow)

                return ReviewResponse(
                    workflow_run_id=workflow_run_id,
                    status="failed",
                    task_type=workflow.task_type or request.task_type,
                    source_type=workflow.source_type or "none",
                    final_decision="failed",
                    summary=f"Workflow failed: {exc}",
                    final_code=final_code,
                    evaluation=final_evaluation,
                    artifacts=context.artifacts,
                    rounds_executed=rounds_executed,
                    steps=context.traces,
                )

    async def _run_agent(
        self,
        *,
        context: WorkflowContext,
        uow: UnitOfWork,
        step_name: str,
        step_order: int,
        round_number: int | None,
        input_data: dict[str, Any],
        runner: Callable[[], Awaitable[tuple[AgentResultT, int]]],
        exclude: set[str] | None = None,
    ) -> AgentResultT:
        started_at = perf_counter()

        try:
            result, latency_ms = await runner()
        except Exception as exc:
            duration_ms = int((perf_counter() - started_at) * 1000)

            await self._trace_agent(
                context=context,
                uow=uow,
                step_name=step_name,
                step_order=step_order,
                round_number=round_number,
                latency_ms=duration_ms,
                status="failed",
                input_data=input_data,
                metadata={},
                detail=str(exc),
            )
            raise

        metadata = result.model_dump(
            mode="json",
            exclude=exclude,
        )

        await self._trace_agent(
            context=context,
            uow=uow,
            step_name=step_name,
            step_order=step_order,
            round_number=round_number,
            latency_ms=latency_ms,
            status="success",
            input_data=input_data,
            metadata=metadata,
            detail=None,
        )

        return result

    @staticmethod
    async def _trace_agent(
        *,
        context: WorkflowContext,
        uow: UnitOfWork,
        step_name: str,
        step_order: int,
        round_number: int | None,
        latency_ms: float | None,
        status: str,
        input_data: dict[str, Any] | None,
        metadata: dict[str, Any],
        detail: str | None,
    ) -> None:
        context.traces.append(
            WorkflowStepTrace(
                step_name=step_name,
                step_type="agent",
                status=status,
                latency_ms=latency_ms,
                round_number=round_number,
                detail=detail,
                metadata=metadata,
            )
        )

        await uow.agent_steps.create(
            AgentStep(
                workflow_id=context.workflow_run_id,
                iteration=round_number or 0,
                step_order=step_order,
                agent_name=step_name,
                duration_ms=(int(latency_ms) if latency_ms is not None else None),
                input_json=input_data,
                output_json=metadata,
                status=status,
                error=detail,
            )
        )

    async def _create_initial_candidate(
        self,
        *,
        request: ReviewRequest,
        router_result: RouterResult,
        requires_generation: bool,
        context: WorkflowContext,
        uow: UnitOfWork,
        step_order: int,
    ) -> CandidateCode:
        """
        Return generated code for a feature request or supplied code
        for a review/refactor workflow.
        """
        if requires_generation:
            writer_output = await self._run_agent(
                context=context,
                uow=uow,
                step_name="code_writer.generate",
                step_order=step_order,
                round_number=0,
                input_data={
                    "instruction": router_result.instruction,
                },
                runner=partial(
                    self.code_writer.run,
                    mode="generate",
                    instruction=router_result.instruction,
                    code=None,
                ),
                exclude={"code"},
            )

            if request.save_artifacts:
                await self._save_artifact(
                    context=context,
                    uow=uow,
                    artifact_type="generated_code",
                    filename="round_0_generated.py",
                    content=writer_output.code,
                )

            return CandidateCode(
                code=writer_output.code,
                origin="code_writer.generate",
                round_number=0,
            )

        if not router_result.code:
            raise ValueError("No code available for review/refactor workflow.")

        if request.save_artifacts:
            await self._save_artifact(
                context=context,
                uow=uow,
                artifact_type="original_code",
                filename="original.py",
                content=router_result.code,
            )

        return CandidateCode(
            code=router_result.code,
            origin="user_input",
            round_number=0,
        )

    @staticmethod
    async def _save_artifact(
        *,
        context: WorkflowContext,
        uow: UnitOfWork,
        artifact_type: str,
        filename: str,
        content: str,
    ) -> None:
        artifact_info = save_artifact(
            context.workflow_run_id,
            artifact_type,
            filename,
            content,
        )
        context.artifacts.append(artifact_info)

        await uow.artifacts.create(
            Artifact(
                workflow_id=context.workflow_run_id,
                artifact_type=artifact_info.artifact_type,
                relative_path=artifact_info.path,
                size_bytes=artifact_info.size_bytes,
            )
        )

    async def _save_round_artifacts(
        self,
        *,
        context: WorkflowContext,
        uow: UnitOfWork,
        round_number: int,
        candidate_code: str,
        tests: str,
        test_result: TestRunResult,
        evaluation: EvaluatorOutput,
    ) -> None:
        await self._save_artifact(
            context=context,
            uow=uow,
            artifact_type="candidate_code",
            filename=f"round_{round_number}_candidate.py",
            content=candidate_code,
        )

        await self._save_artifact(
            context=context,
            uow=uow,
            artifact_type="generated_tests",
            filename=f"round_{round_number}_tests.py",
            content=tests,
        )

        await self._save_artifact(
            context=context,
            uow=uow,
            artifact_type="test_report",
            filename=f"round_{round_number}_test_report.json",
            content=test_result.model_dump_json(indent=2),
        )

        await self._save_artifact(
            context=context,
            uow=uow,
            artifact_type="evaluation_report",
            filename=f"round_{round_number}_evaluation.json",
            content=evaluation.model_dump_json(indent=2),
        )


async def run_code_workflow(request: ReviewRequest) -> ReviewResponse:
    workflow_settings = get_workflow_settings()

    workflow_config = WorkflowConfig(
        max_rounds=(
            request.max_rounds
            if request.max_rounds is not None
            else workflow_settings.workflow_max_rounds
        ),
        force_retry_rounds=workflow_settings.workflow_force_retry_rounds,
        always_retry=workflow_settings.workflow_always_retry,
    )

    workflow = CodeWorkflow(config=workflow_config)

    return await workflow.run(request)
