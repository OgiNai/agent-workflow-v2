"""LLM-as-judge evaluator agent."""

from apps.agents.base_agent import BaseAgent
from apps.core.settings import LLMSettings
from apps.llm.agent_requiremenrs import EVALUATOR_DECISION_POLICY
from apps.llm.prompts import EVALUATOR_PROMPT, PROMPT_VERSIONS
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
        llm_settings: LLMSettings | None = None,
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
            "decision_policy": EVALUATOR_DECISION_POLICY,
        }

        result, latency_ms = await self._run_structured(
            system_instruction=EVALUATOR_PROMPT,
            payload=payload,
            response_schema=EvaluatorOutput,
            prompt_version=PROMPT_VERSIONS["evaluator"],
            llm_settings=llm_settings if llm_settings else LLMSettings(),
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
