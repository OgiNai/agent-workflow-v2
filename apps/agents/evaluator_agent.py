"""LLM-as-judge evaluator agent."""

from apps.agents.base_agent import BaseAgent
from apps.llm.prompts import EVALUATOR_PROMPT
from apps.schemas.agent_outputs import (
    EvaluatorOutput,
    ReviewerOutput,
    SecurityAuditOutput,
)
from apps.schemas.tools import TestRunResult


class EvaluatorAgent(BaseAgent):
    agent_name = "evaluator"

    async def run(
        self,
        *,
        instruction: str,
        code: str,
        review: ReviewerOutput,
        security: SecurityAuditOutput,
        test_result: TestRunResult,
        rule_score: float,
        rule_notes: list[str],
        execution_score: float,
        round_number: int,
    ) -> tuple[EvaluatorOutput, int]:
        payload = {
            "instruction": instruction,
            "candidate_code": code,
            "review": review.model_dump(),
            "security": security.model_dump(),
            "test_result": test_result.model_dump(),
            "rule_score": rule_score,
            "rule_notes": rule_notes,
            "execution_score": execution_score,
            "round_number": round_number,
            "decision_policy": {
                "pass": "Use when no blocking correctness or security issues remain and required tests pass.",
                "pass_with_warnings": "Use when no blocking issues remain, but non-critical recommendations still exist.",
                "retry": "Use whenever blocking correctness, security, execution, or test issues remain.",
            },
        }

        result, latency_ms = await self._run_structured(
            system_instruction=EVALUATOR_PROMPT,
            payload=payload,
            response_schema=EvaluatorOutput,
        )
        calculated_llm_score = round(
            0.35 * result.security_score
            + 0.30 * result.maintainability_score
            + 0.35 * result.correctness_score,
            3,
        )
        calculated_final_score = round(
            0.25 * rule_score + 0.45 * execution_score + 0.30 * calculated_llm_score, 3
        )

        # overwrite rule_score and execution_score to make sure LLM has not changed them
        # record calculated llm and final scores
        result = result.model_copy(
            update={
                "rule_score": rule_score,
                "execution_score": execution_score,
                "llm_score": calculated_llm_score,
                "final_score": calculated_final_score,
            }
        )

        return result, latency_ms
