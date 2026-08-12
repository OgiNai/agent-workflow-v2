"""Base LLM agent abstractions."""

import json
import logging
import time
from typing import Any, TypeVar

from pydantic import BaseModel

from apps.llm.gemini_client import DEFAULT_MODEL, generate_structured

logger = logging.getLogger(__name__)
ResponseSchemaT = TypeVar("ResponseSchemaT", bound=BaseModel)


class BaseAgent:
    """Common wrapper for schema-based LLM agent calls."""

    agent_name: str = "base_agent"
    model_name: str = DEFAULT_MODEL
    temperature: float = 0.2

    async def _run_structured(
        self,
        *,
        system_instruction: str,
        payload: dict[str, Any],
        response_schema: type[ResponseSchemaT],
    ) -> tuple[ResponseSchemaT, int]:
        """Run a structured LLM call and return output plus latency."""
        started = time.perf_counter()
        prompt = json.dumps(payload, ensure_ascii=False, indent=2)
        result = await generate_structured(
            system_instruction=system_instruction,
            prompt=prompt,
            response_schema=response_schema,
            model_name=self.model_name,
            temperature=self.temperature,
        )
        latency_ms = int((time.perf_counter() - started) * 1000)
        logger.info(
            "agent_call_completed",
            extra={"agent_name": self.agent_name, "latency_ms": latency_ms},
        )
        return result, latency_ms
