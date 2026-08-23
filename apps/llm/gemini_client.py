"""Shared Gemini client helpers."""

from __future__ import annotations

import json
import logging
from contextvars import ContextVar
from dataclasses import dataclass
from typing import TypeVar

from google import genai
from google.genai import types
from pydantic import BaseModel, ValidationError

from apps.core.settings import LLMSettings, get_auth_settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)
_client: genai.Client | None = None
DEFAULT_MODEL = "gemini-3.1-flash-lite"


@dataclass(frozen=True)
class LLMUsage:
    """Provider-neutral token usage information."""

    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    cached_tokens: int | None = None


# store data specific to a single async task or thread without letting other
# tasks or threads see or change its own value
_last_llm_usage: ContextVar[LLMUsage | None] = ContextVar(
    "last_llm_usage",
    default=None,
)


def get_last_llm_usage() -> LLMUsage | None:
    """Return token usage for the most recent LLM call in this task."""
    return _last_llm_usage.get()


def _set_llm_usage(usage: LLMUsage | None) -> None:
    _last_llm_usage.set(usage)


def _extract_usage(response: object) -> LLMUsage:
    """Extract provider usage metadata without exposing SDK types downstream."""
    usage_metadata = getattr(response, "usage_metadata", None)

    if usage_metadata is None:
        return LLMUsage()

    return LLMUsage(
        prompt_tokens=getattr(
            usage_metadata,
            "prompt_token_count",
            None,
        ),
        completion_tokens=getattr(
            usage_metadata,
            "candidates_token_count",
            None,
        ),
        total_tokens=getattr(
            usage_metadata,
            "total_token_count",
            None,
        ),
        cached_tokens=getattr(
            usage_metadata,
            "cached_content_token_count",
            None,
        ),
    )


def _get_gemini_client(llm_settings: LLMSettings) -> genai.Client:
    """Create the Gemini client lazily so FastAPI startup stays lightweight."""
    global _client
    if _client is None:
        _client = genai.Client(
            http_options=types.HttpOptions(
                retry_options=types.HttpRetryOptions(
                    initial_delay=llm_settings.initial_delay,
                    attempts=llm_settings.attempts,
                )
            ),
            api_key=get_auth_settings().gemini_api_key.get_secret_value(),
        )
    return _client


async def generate_text(
    *,
    system_instruction: str,
    prompt: str,
    model_name: str = DEFAULT_MODEL,
    llm_settings: LLMSettings | None = None,
) -> str:
    """Call Gemini and return raw text."""

    _set_llm_usage(None)

    response = await _get_gemini_client(llm_settings).aio.models.generate_content(
        model=model_name,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=llm_settings.temperature,
        ),
        contents=prompt,
    )
    _set_llm_usage(_extract_usage(response))
    return response.text or ""


async def generate_structured(
    *,
    system_instruction: str,
    prompt: str,
    response_schema: type[T],
    model_name: str = DEFAULT_MODEL,
    llm_settings: LLMSettings | None = None,
) -> T:
    """Call Gemini with a Pydantic response schema and parse the result."""

    _set_llm_usage(None)

    response = await _get_gemini_client(llm_settings).aio.models.generate_content(
        model=model_name,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=llm_settings.temperature,
            response_mime_type="application/json",
            response_schema=response_schema,
        ),
        contents=prompt,
    )
    _set_llm_usage(_extract_usage(response))

    raw = response.text or "{}"
    try:
        return response_schema.model_validate_json(raw)
    except ValidationError:
        logger.exception(
            "structured_model_parsing_failed",
            extra={
                "model_name": model_name,
                "response_schema": response_schema.__name__,
            },
        )
        return response_schema.model_validate(json.loads(raw))


async def close_gemini_client() -> None:
    """Close the async Gemini client during FastAPI shutdown."""
    global _client

    if _client is not None:
        await _client.aio.aclose()
        _client = None
