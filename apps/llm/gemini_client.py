"""Shared Gemini client helpers."""

#import asyncio
import json
import logging
from typing import TypeVar

from google import genai
from google.genai import types
from pydantic import BaseModel

from apps.core.settings import get_auth_settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)
_client: genai.Client | None = None
DEFAULT_MODEL = "gemini-3.1-flash-lite"


def _get_gemini_client() -> genai.Client:
    """Create the Gemini client lazily so FastAPI startup stays lightweight."""
    global _client
    if _client is None:
        _client = genai.Client(
            http_options=types.HttpOptions(
                retry_options=types.HttpRetryOptions(initial_delay=5, attempts=3)
            ),
            api_key=get_auth_settings().gemini_api_key.get_secret_value(),
        )
    return _client


async def generate_text(
    *,
    system_instruction: str,
    prompt: str,
    model_name: str = DEFAULT_MODEL,
    temperature: float = 0.2,
) -> str:
    """Call Gemini and return raw text."""

    response = await _get_gemini_client().aio.models.generate_content(
        model=model_name,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
        ),
        contents=prompt,
    )
    return response.text or ""


async def generate_structured(
    *,
    system_instruction: str,
    prompt: str,
    response_schema: type[T],
    model_name: str = DEFAULT_MODEL,
    temperature: float = 0.2,
) -> T:
    """Call Gemini with a Pydantic response schema and parse the result."""

    response = await _get_gemini_client().aio.models.generate_content(
        model=model_name,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
            response_mime_type="application/json",
            response_schema=response_schema,
        ),
        contents=prompt,
    )

    raw = response.text or "{}"
    try:
        return response_schema.model_validate_json(raw)
    except Exception:
        logger.warning("Structured model parsing failed; raw response=%s", raw)
        return response_schema.model_validate(json.loads(raw))

async def close_gemini_client() -> None:
    """Close the async Gemini client during FastAPI shutdown."""
    global _client

    if _client is not None:
        await _client.aio.aclose()
        _client = None