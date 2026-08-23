"""Code writer agent used for generate, refactor, and repair modes."""

from typing import Literal

from apps.agents.base_agent import BaseAgent
from apps.core.settings import LLMSettings
from apps.llm.agent_requiremenrs import CODE_WRITER_REQUIREMENTS
from apps.llm.prompts import CODE_WRITER_PROMPTS, PROMPT_VERSIONS
from apps.schemas.agent_outputs import (
    CodeWriterOutput,
    EvaluatorOutput,
    ReviewerOutput,
    SecurityAuditOutput,
)

CodeWriterMode = Literal["generate", "refactor", "repair"]


class CodeWriterAgent(BaseAgent):
    agent_name = "code_writer"

    async def run(
        self,
        *,
        mode: CodeWriterMode,
        instruction: str,
        code: str | None = None,
        review: ReviewerOutput | None = None,
        security: SecurityAuditOutput | None = None,
        evaluation: EvaluatorOutput | None = None,
        llm_settings: LLMSettings | None = None,
    ) -> tuple[CodeWriterOutput, int]:
        payload = {
            "mode": mode,
            "instruction": instruction,
            "candidate_code": code,
            "review_feedback": review.model_dump() if review else None,
            "security_feedback": security.model_dump() if security else None,
            "evaluation_feedback": evaluation.model_dump() if evaluation else None,
            "requirements": CODE_WRITER_REQUIREMENTS,
        }
        return await self._run_structured(
            system_instruction=CODE_WRITER_PROMPTS[mode],
            payload=payload,
            response_schema=CodeWriterOutput,
            prompt_version=PROMPT_VERSIONS[f"code_writer.{mode}"],
            llm_settings=llm_settings if llm_settings else LLMSettings(),
        )
