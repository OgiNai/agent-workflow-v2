"""LLM agent for pytest generation."""

from apps.agents.base_agent import BaseAgent
from apps.llm.prompts import TEST_GENERATOR_PROMPT
from apps.schemas.agent_outputs import TestGeneratorOutput


class TestGeneratorAgent(BaseAgent):
    agent_name = "test_generator"

    async def run(self, *, instruction: str, code: str) -> tuple[TestGeneratorOutput, int]:
        payload = {
            "instruction": instruction,
            "candidate_code": code,
            "requirements": [
                "Use pytest.",
                "Assume candidate code is stored in solution.py.",
                "Import from solution, e.g. from solution import function_name.",
                "Do not include markdown fences.",
            ],
        }
        return await self._run_structured(
            system_instruction=TEST_GENERATOR_PROMPT,
            payload=payload,
            response_schema=TestGeneratorOutput,
        )
