"""Reusable inspection agent for reviewer and security-auditor modes."""

from typing import Literal, overload

from apps.agents.base_agent import BaseAgent
from apps.llm.prompts import INSPECTION_PROMPTS
from apps.schemas.agent_outputs import ReviewerOutput, SecurityAuditOutput

InspectionMode = Literal["reviewer", "security_auditor"]


class InspectionAgent(BaseAgent):
    agent_name = "inspection"

    @overload
    async def run(self, *, mode: Literal["reviewer"], instruction: str, code: str) -> tuple[ReviewerOutput, int]: ...

    @overload
    async def run(self, *, mode: Literal["security_auditor"], instruction: str, code: str) -> tuple[SecurityAuditOutput, int]: ...

    async def run(self, *, mode: InspectionMode, instruction: str, code: str) -> tuple[ReviewerOutput | SecurityAuditOutput, int]:
        schema = ReviewerOutput if mode == "reviewer" else SecurityAuditOutput
        payload = {
            "mode": mode,
            "instruction": instruction,
            "candidate_code": code,
            "requirements": [
                "Inspect the candidate code only.",
                "Do not rewrite the full code.",
                "Return concrete findings, not generic advice.",
            ],
        }
        return await self._run_structured(
            system_instruction=INSPECTION_PROMPTS[mode],
            payload=payload,
            response_schema=schema,
        )
