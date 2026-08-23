"""LLM agent for pytest generation."""

from apps.agents.base_agent import BaseAgent
from apps.core.settings import LLMSettings
from apps.llm.agent_requiremenrs import TEST_GENERATOR_REQUIREMENTS
from apps.llm.prompts import PROMPT_VERSIONS, TEST_GENERATOR_PROMPT
from apps.schemas.agent_outputs import TestGeneratorOutput


class TestGeneratorAgent(BaseAgent):
    agent_name = "test_generator"

    async def run(
        self,
        *,
        instruction: str,
        code: str,
        llm_settings: LLMSettings | None = None,
    ) -> tuple[TestGeneratorOutput, int]:
        payload = {
            "instruction": instruction,
            "candidate_code": code,
            "requirements": TEST_GENERATOR_REQUIREMENTS,
        }
        return await self._run_structured(
            system_instruction=TEST_GENERATOR_PROMPT,
            payload=payload,
            response_schema=TestGeneratorOutput,
            prompt_version=PROMPT_VERSIONS["test_generator"],
            llm_settings=llm_settings if llm_settings is not None else LLMSettings(),
        )
