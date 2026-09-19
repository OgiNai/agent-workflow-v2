"""Tests for LLM configuration validation."""

import pytest
from pydantic import ValidationError

from apps.core.settings import LLMSettings


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("attempts", 0),
        ("initial_delay", 0),
        ("temperature", -0.1),
        ("temperature", 2.1),
    ],
)
def test_llm_settings_reject_invalid_values(
    field: str,
    value: float,
) -> None:
    with pytest.raises(ValidationError):
        LLMSettings(**{field: value})


def test_llm_settings_require_non_empty_model_name() -> None:
    with pytest.raises(ValidationError):
        LLMSettings(model_name="")
