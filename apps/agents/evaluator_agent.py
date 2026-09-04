"""LLM-as-judge evaluator agent."""

from apps.agents.base_agent import BaseAgent
from apps.core.settings import LLMSettings
from apps.evals.decision_policy import determine_decision
from apps.evals.scoring import calculate_final_score, calculate_llm_score
from apps.llm.prompts import EVALUATOR_PROMPT, PROMPT_VERSIONS
from apps.schemas.agent_outputs import (
    EvaluatorOutput,
    Finding,
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
        findings = [
            *review.findings,
            *security.findings,
        ]

        payload = {
            "instruction": instruction,
            "candidate_code": code,
            "review_findings": [
                finding.model_dump(mode="json") for finding in review.findings
            ],
            "security_findings": [
                finding.model_dump(mode="json") for finding in security.findings
            ],
            "findings": [finding.model_dump(mode="json") for finding in findings],
            "test_result": test_result.model_dump(mode="json"),
            "rule_score": rule_score,
            "rule_notes": rule_notes,
            "execution_score": execution_score,
            "round_number": round_number,
        }

        result, latency_ms = await self._run_structured(
            system_instruction=EVALUATOR_PROMPT,
            payload=payload,
            response_schema=EvaluatorOutput,
            prompt_version=PROMPT_VERSIONS["evaluator"],
            llm_settings=llm_settings if llm_settings else LLMSettings(),
        )

        result = self._normalize_findings(
            result=result,
            original_findings=findings,
        )

        llm_score = calculate_llm_score(
            correctness_score=result.correctness_score,
            security_score=result.security_score,
            maintainability_score=result.maintainability_score,
        )

        final_score = calculate_final_score(
            rule_score=rule_score,
            execution_score=execution_score,
            llm_score=llm_score,
        )

        final_decision = determine_decision(
            final_score=final_score,
            test_result=test_result,
            findings=result.findings,
        )

        # overwrite rule_score and execution_score to make sure LLM has not changed them
        # record calculated llm and final scores
        result = result.model_copy(
            update={
                "rule_score": rule_score,
                "execution_score": execution_score,
                "llm_score": llm_score,
                "final_score": final_score,
                "final_decision": final_decision,
            }
        )

        return result, latency_ms

    @staticmethod
    def _normalize_findings(
        *,
        result: EvaluatorOutput,
        original_findings: list[Finding],
    ) -> EvaluatorOutput:
        """Ensure evaluator findings correspond to original findings."""

        evaluated_by_id = {finding.id: finding for finding in result.findings}

        normalized_findings: list[Finding] = []

        for original in original_findings:
            evaluated = evaluated_by_id.get(original.id)

            if evaluated is None:
                normalized_findings.append(
                    original.model_copy(update={"status": "unresolved"})
                )
                continue

            normalized_findings.append(
                original.model_copy(
                    update={
                        "status": evaluated.status,
                    }
                )
            )

        return result.model_copy(update={"findings": normalized_findings})
