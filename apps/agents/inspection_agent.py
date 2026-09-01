"""Reusable inspection agent for reviewer and security-auditor modes."""

from hashlib import sha256
from typing import Literal, overload

from apps.agents.base_agent import BaseAgent
from apps.core.settings import LLMSettings
from apps.llm.agent_requiremenrs import INSPECTION_REQUIREMENTS
from apps.llm.prompts import INSPECTION_PROMPTS, PROMPT_VERSIONS
from apps.schemas.agent_outputs import Finding, ReviewerOutput, SecurityAuditOutput

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
        result, latency_ms = await self._run_structured(
            system_instruction=INSPECTION_PROMPTS[mode],
            payload=payload,
            response_schema=schema,
            prompt_version=PROMPT_VERSIONS[f"inspection.{mode}"],
            llm_settings=llm_settings if llm_settings else LLMSettings(),
        )

        result = self._normalize_findings(result)

        return result, latency_ms

    @staticmethod
    def _normalize_findings(
        result: ReviewerOutput | SecurityAuditOutput,
    ) -> ReviewerOutput | SecurityAuditOutput:
        """Assign stable application-generated IDs to inspection findings."""

        normalized_findings = [
            finding.model_copy(
                update={
                    "id": InspectionAgent._finding_id(finding),
                    "status": "unresolved",
                }
            )
            for finding in result.findings
        ]

        return result.model_copy(update={"findings": normalized_findings})

    @staticmethod
    def _finding_id(finding: Finding) -> str:
        """Generate a stable ID from the semantic content of a finding."""

        normalized = "|".join(
            (
                finding.category.strip().lower(),
                finding.severity,
                finding.description.strip().lower(),
            )
        )

        digest = sha256(normalized.encode("utf-8")).hexdigest()

        return f"finding_{digest[:16]}"
