"""Unified code generation/review/refactoring workflow."""

from __future__ import annotations

import logging
from uuid import uuid4

from apps.agents.code_writer_agent import CodeWriterAgent
from apps.agents.evaluator_agent import EvaluatorAgent
from apps.agents.inspection_agent import InspectionAgent
from apps.agents.planner_agent import PlannerAgent
from apps.agents.test_generator_agent import TestGeneratorAgent
from apps.evals.execution_eval import calculate_execution_score
from apps.evals.rule_based import calculate_rule_score
from apps.schemas.agent_outputs import (
    EvaluatorOutput,  # , ReviewerOutput, SecurityAuditOutput
)
from apps.schemas.requests import ReviewRequest
from apps.schemas.responses import ReviewResponse
from apps.schemas.workflow import (  # , ArtifactInfo
    CandidateCode,
    RouterResult,
    WorkflowContext,
    WorkflowStepTrace,
)
from apps.tools.test_runner import TestRunResult, run_pytest_for_code
from apps.workflows.artifact_manager import save_artifact
from apps.workflows.input_router import route_input
from apps.workflows.retry_policy import should_retry

logger = logging.getLogger(__name__)


class CodeWorkflow:
    """Orchestrates the unified workflow for both feature requests and code review requests."""

    # def __init__(self) -> None:
    #    self.planner = PlannerAgent()
    #    self.code_writer = CodeWriterAgent()
    #    self.inspector = InspectionAgent()
    #    self.test_generator = TestGeneratorAgent()
    #    self.evaluator = EvaluatorAgent()

    def __init__(
        self,
        *,
        planner: PlannerAgent | None = None,
        code_writer: CodeWriterAgent | None = None,
        inspector: InspectionAgent | None = None,
        test_generator: TestGeneratorAgent | None = None,
        evaluator: EvaluatorAgent | None = None,
        # test_runner: TestRunner,
        # artifact_manager: ArtifactManager,
    ) -> None:
        self.planner = planner or PlannerAgent()
        self.code_writer = code_writer or CodeWriterAgent()
        self.inspector = inspector or InspectionAgent()
        self.test_generator = test_generator or TestGeneratorAgent()
        self.evaluator = evaluator or EvaluatorAgent()
        # self.test_runner = test_runner
        # self.artifact_manager = artifact_manager

    async def run(self, request: ReviewRequest) -> ReviewResponse:
        workflow_run_id = uuid4()
        context = WorkflowContext(
            workflow_run_id=workflow_run_id, request_id=str(workflow_run_id)
        )
        rounds_executed = 0
        final_evaluation: EvaluatorOutput | None = None
        final_code: str | None = None
        final_summary = "Workflow did not complete."

        try:
            router_result = route_input(request)
            context.traces.append(
                WorkflowStepTrace(
                    step_name="input_router",
                    step_type="workflow",
                    status="success",
                    detail=f"Resolved {router_result.source_type} -> {router_result.task_type}",
                )
            )

            plan, planner_output, planner_latency = await self.planner.run(
                router_result, request.max_rounds
            )
            context.traces.append(
                WorkflowStepTrace(
                    step_name="planner",
                    step_type="agent",
                    status="success",
                    latency_ms=planner_latency,
                    metadata=planner_output.model_dump(),
                )
            )

            candidate = await self._create_initial_candidate(
                request, router_result, plan.requires_generation, context
            )
            previous_evaluation: EvaluatorOutput | None = None

            for round_number in range(1, plan.max_rounds + 1):
                rounds_executed = round_number
                review, review_latency = await self.inspector.run(
                    mode="reviewer",
                    instruction=router_result.instruction,
                    code=candidate.code,
                )
                self._trace_agent(
                    context,
                    step_name="inspection.reviewer",
                    latency_ms=review_latency,
                    round_number=round_number,
                    metadata=review.model_dump(),
                )

                security, security_latency = await self.inspector.run(
                    mode="security_auditor",
                    instruction=router_result.instruction,
                    code=candidate.code,
                )
                self._trace_agent(
                    context,
                    step_name="inspection.security_auditor",
                    latency_ms=security_latency,
                    round_number=round_number,
                    metadata=security.model_dump(),
                )

                writer_mode = "refactor" if round_number == 1 else "repair"
                writer_output, writer_latency = await self.code_writer.run(
                    mode=writer_mode,
                    instruction=router_result.instruction,
                    code=candidate.code,
                    review=review,
                    security=security,
                    evaluation=previous_evaluation,
                )
                candidate = CandidateCode(
                    code=writer_output.code,
                    origin=f"code_writer.{writer_mode}",
                    round_number=round_number,
                )
                final_code = candidate.code
                self._trace_agent(
                    context,
                    step_name=f"code_writer.{writer_mode}",
                    latency_ms=writer_latency,
                    round_number=round_number,
                    metadata=writer_output.model_dump(exclude={"code"}),
                )

                tests_output, tests_latency = await self.test_generator.run(
                    instruction=router_result.instruction,
                    code=candidate.code,
                )
                self._trace_agent(
                    context,
                    step_name="test_generator",
                    latency_ms=tests_latency,
                    round_number=round_number,
                    metadata=tests_output.model_dump(exclude={"tests"}),
                )

                test_result = await run_pytest_for_code(
                    candidate.code, tests_output.tests
                )
                context.traces.append(
                    WorkflowStepTrace(
                        step_name="test_runner",
                        step_type="tool",
                        status="success"
                        if test_result.status == "passed"
                        else "failed",
                        latency_ms=test_result.duration_ms,
                        round_number=round_number,
                        metadata=test_result.model_dump(),
                    )
                )

                rule_score, rule_notes = calculate_rule_score(candidate.code, security)
                execution_score = calculate_execution_score(test_result)
                evaluation, evaluation_latency = await self.evaluator.run(
                    instruction=router_result.instruction,
                    code=candidate.code,
                    review=review,
                    security=security,
                    test_result=test_result,
                    rule_score=rule_score,
                    execution_score=execution_score,
                    round_number=round_number,
                    # max_rounds=plan.max_rounds,
                )
                evaluation.reasons.extend(rule_notes)
                # if round_number >= plan.max_rounds and evaluation.final_decision == "retry":
                #    evaluation.final_decision = "fail"
                #    evaluation.reasons.append("Max rounds reached; retry converted to fail.")

                final_evaluation = evaluation
                previous_evaluation = evaluation
                context.traces.append(
                    WorkflowStepTrace(
                        step_name="evaluator",
                        step_type="agent",
                        status="success",
                        latency_ms=evaluation_latency,
                        round_number=round_number,
                        metadata=evaluation.model_dump(),
                    )
                )

                if request.save_artifacts:
                    self._save_round_artifacts(
                        context=context,
                        round_number=round_number,
                        candidate_code=candidate.code,
                        tests=tests_output.tests,
                        test_result=test_result,
                        evaluation=evaluation,
                    )

                if evaluation.final_decision in {"pass", "pass_with_warnings"}:
                    final_summary = "Workflow completed successfully."
                    break

                if not should_retry(evaluation, round_number, plan.max_rounds):
                    final_summary = "Workflow completed without passing evaluation."
                    break

                context.traces.append(
                    WorkflowStepTrace(
                        step_name="retry_policy",
                        step_type="workflow",
                        status="success",
                        round_number=round_number,
                        detail="Retry routes back to Reviewer with latest candidate code.",
                    )
                )
            final_decision = self._resolve_final_decision(final_evaluation)
            status = (
                "completed"
                if final_decision in {"pass", "pass_with_warnings"}
                else "completed_with_warnings"
            )
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
            context.traces.append(
                WorkflowStepTrace(
                    step_name="workflow",
                    step_type="workflow",
                    status="failed",
                    detail=str(exc),
                )
            )
            return ReviewResponse(
                workflow_run_id=workflow_run_id,
                status="failed",
                task_type=request.task_type,
                source_type="none",  # request.input_type,
                final_decision="failed",
                summary=f"Workflow failed: {exc}",
                final_code=final_code,
                evaluation=final_evaluation,
                artifacts=context.artifacts,
                rounds_executed=rounds_executed,
                steps=context.traces,
            )

    async def _create_initial_candidate(
        self,
        request: ReviewRequest,
        router_result: RouterResult,
        requires_generation: bool,
        context: WorkflowContext,
    ) -> CandidateCode:
        """
        Returns either generated code if request is for new feature or original code provided
        in the request
        """
        if requires_generation:
            writer_output, writer_latency = await self.code_writer.run(
                mode="generate",
                instruction=router_result.instruction,
                code=None,  # router_result.original_content,
            )
            self._trace_agent(
                context,
                step_name="code_writer.generate",
                latency_ms=writer_latency,
                round_number=0,
                metadata=writer_output.model_dump(exclude={"code"}),
            )
            if request.save_artifacts:
                artifact = save_artifact(
                    context.workflow_run_id,
                    "generated_code",
                    "round_0_generated.py",
                    writer_output.code,
                )
                context.artifacts.append(artifact)
            return CandidateCode(
                code=writer_output.code, origin="code_writer.generate", round_number=0
            )

        if not router_result.code:
            raise ValueError("No code available for review/refactor workflow.")

        if request.save_artifacts:
            artifact = save_artifact(
                context.workflow_run_id,
                "original_code",
                "original.py",
                router_result.code,
            )
            context.artifacts.append(artifact)
        return CandidateCode(
            code=router_result.code, origin="user_input", round_number=0
        )

    @staticmethod
    def _resolve_final_decision(evaluation: EvaluatorOutput | None) -> str:

        if evaluation.final_decision in {"pass", "pass_with_warnings"}:
            return evaluation.final_decision

        return "unresolved"

    @staticmethod
    def _trace_agent(
        context: WorkflowContext,
        *,
        step_name: str,
        latency_ms: int,
        round_number: int | None,
        metadata: dict,
    ) -> None:
        context.traces.append(
            WorkflowStepTrace(
                step_name=step_name,
                step_type="agent",
                status="success",
                latency_ms=latency_ms,
                round_number=round_number,
                metadata=metadata,
            )
        )

    @staticmethod
    def _save_round_artifacts(
        *,
        context: WorkflowContext,
        round_number: int,
        candidate_code: str,
        tests: str,
        test_result: TestRunResult,
        evaluation: EvaluatorOutput,
    ) -> None:
        context.artifacts.append(
            save_artifact(
                context.workflow_run_id,
                "candidate_code",
                f"round_{round_number}_candidate.py",
                candidate_code,
            )
        )
        context.artifacts.append(
            save_artifact(
                context.workflow_run_id,
                "generated_tests",
                f"round_{round_number}_tests.py",
                tests,
            )
        )
        context.artifacts.append(
            save_artifact(
                context.workflow_run_id,
                "test_report",
                f"round_{round_number}_test_report.json",
                test_result.model_dump_json(indent=2),
            )
        )
        context.artifacts.append(
            save_artifact(
                context.workflow_run_id,
                "evaluation_report",
                f"round_{round_number}_evaluation.json",
                evaluation.model_dump_json(indent=2),
            )
        )


async def run_code_workflow(request: ReviewRequest) -> ReviewResponse:
    workflow = CodeWorkflow()
    return await workflow.run(request)
