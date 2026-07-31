"""Code writer agent used for generate, refactor, and repair modes."""

from typing import Literal

from apps.agents.base_agent import BaseAgent
from apps.llm.prompts import CODE_WRITER_PROMPTS
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
    ) -> tuple[CodeWriterOutput, int]:
        payload = {
            "mode": mode,
            "instruction": instruction,
            "candidate_code": code,
            "review_feedback": review.model_dump() if review else None,
            "security_feedback": security.model_dump() if security else None,
            "evaluation_feedback": evaluation.model_dump() if evaluation else None,
            "requirements": [
                "Return complete Python code in the code field.",
                "Do not wrap code in markdown fences.",
                "Prefer type hints and clear errors.",
                "Do not introduce external dependencies unless required by the instruction.",
            ],
        }
        return await self._run_structured(
            system_instruction=CODE_WRITER_PROMPTS[mode],
            payload=payload,
            response_schema=CodeWriterOutput,
        )
