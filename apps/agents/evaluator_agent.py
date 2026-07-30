"""LLM-as-judge evaluator agent."""

from apps.agents.base_agent import BaseAgent
from apps.llm.prompts import EVALUATOR_PROMPT
from apps.schemas.agent_outputs import (
    EvaluatorOutput,
    ReviewerOutput,
    SecurityAuditOutput,
)
from apps.tools.test_runner import TestRunResult


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
        execution_score: float,
        round_number: int,
        # max_rounds: int,
    ) -> tuple[EvaluatorOutput, int]:
        payload = {
            "instruction": instruction,
            "candidate_code": code,
            "review": review.model_dump(),
            "security": security.model_dump(),
            "test_result": test_result.model_dump(),
            "rule_score": rule_score,
            "execution_score": execution_score,
            "round_number": round_number,
            # "max_rounds": max_rounds,
            "decision_policy": {
                "pass": "Use when no blocking correctness or security issues remain and required tests pass.",
                "pass_with_warnings": "Use when no blocking issues remain, but non-critical recommendations still exist.",
                "retry": "Use whenever blocking correctness, security, execution, or test issues remain.",
                # "fail": "Use when severe issues remain or max rounds are exhausted.",
            },
        }
        return await self._run_structured(
            system_instruction=EVALUATOR_PROMPT,
            payload=payload,
            response_schema=EvaluatorOutput,
        )
