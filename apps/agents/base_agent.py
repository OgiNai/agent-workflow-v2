"""Base LLM agent abstractions."""

import json
import logging
import time
from typing import Any, TypeVar

from opentelemetry.trace import SpanKind, Status, StatusCode
from pydantic import BaseModel

from apps.core.settings import LLMSettings
from apps.llm.gemini_client import DEFAULT_MODEL, generate_structured
from apps.observability.telemetry import get_tracer

logger = logging.getLogger(__name__)
ResponseSchemaT = TypeVar("ResponseSchemaT", bound=BaseModel)


class BaseAgent:
    """Common wrapper for schema-based LLM agent calls."""

    agent_name: str = "base_agent"
    model_name: str = DEFAULT_MODEL

    async def _run_structured(
        self,
        *,
        system_instruction: str,
        payload: dict[str, Any],
        response_schema: type[ResponseSchemaT],
        prompt_version: str,
        llm_settings: LLMSettings | None = None,
    ) -> tuple[ResponseSchemaT, int]:
        """Run a structured LLM call and return output plus latency."""

        started = time.perf_counter()

        tracer = get_tracer("apps.agents")

        # Each LLM call creates a child span under the workflow span
        # and records model/prompt-version information.
        with tracer.start_as_current_span(
            f"agent.{self.agent_name}",
            kind=SpanKind.CLIENT,
            attributes={
                "agent.name": self.agent_name,
                "llm.provider": "google",
                "llm.model": self.model_name,
                "prompt.version": prompt_version,
                "temperature": llm_settings.temperature,
            },
        ) as span:
            prompt = json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
            )

            try:
                result = await generate_structured(
                    system_instruction=system_instruction,
                    prompt=prompt,
                    response_schema=response_schema,
                    model_name=self.model_name,
                    temperature=llm_settings.temperature,
                    llm_settings=llm_settings,
                )
            except Exception as exc:
                span.record_exception(exc)
                span.set_status(
                    Status(
                        StatusCode.ERROR,
                        str(exc),
                    )
                )
                raise

            latency_ms = int((time.perf_counter() - started) * 1000)

            span.set_attribute(
                "llm.latency_ms",
                latency_ms,
            )

            logger.info(
                "agent_call_completed",
                extra={
                    "agent_name": self.agent_name,
                    "latency_ms": latency_ms,
                    "model_name": self.model_name,
                    "prompt_version": prompt_version,
                },
            )

            return result, latency_ms
