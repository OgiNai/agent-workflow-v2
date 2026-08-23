"""Reusable inspection agent for reviewer and security-auditor modes."""

from typing import Literal, overload

from apps.agents.base_agent import BaseAgent
from apps.core.settings import LLMSettings
from apps.llm.agent_requiremenrs import INSPECTION_REQUIREMENTS
from apps.llm.prompts import INSPECTION_PROMPTS, PROMPT_VERSIONS
from apps.schemas.agent_outputs import ReviewerOutput, SecurityAuditOutput

InspectionMode = Literal["reviewer", "security_auditor"]


class InspectionAgent(BaseAgent):
    agent_name = "inspection"

    @overload
    async def run(
        self,
        *,
        mode: Literal["reviewer"],
        instruction: str,
        code: str,
        llm_settings: LLMSettings | None = None,
    ) -> tuple[ReviewerOutput, int]: ...

    @overload
    async def run(
        self,
        *,
        mode: Literal["security_auditor"],
        instruction: str,
        code: str,
        llm_settings: LLMSettings | None = None,
    ) -> tuple[SecurityAuditOutput, int]: ...

    async def run(
        self,
        *,
        mode: InspectionMode,
        instruction: str,
        code: str,
        llm_settings: LLMSettings | None = None,
    ) -> tuple[ReviewerOutput | SecurityAuditOutput, int]:
        schema = ReviewerOutput if mode == "reviewer" else SecurityAuditOutput
        payload = {
            "mode": mode,
            "instruction": instruction,
            "candidate_code": code,
            "requirements": INSPECTION_REQUIREMENTS,
        }
        return await self._run_structured(
            system_instruction=INSPECTION_PROMPTS[mode],
            payload=payload,
            response_schema=schema,
            prompt_version=PROMPT_VERSIONS[f"inspection.{mode}"],
            llm_settings=llm_settings if llm_settings is not None else LLMSettings(),
        )
