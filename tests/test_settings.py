"""Configuration settings tests."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from apps.core.settings import (
    AuthSettings,
    WorkflowSettings,
    # get_auth_settings,
    # get_workflow_settings,
)


def test_auth_settings_load_environment_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("API_TOKEN", "test-api-token")
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://user:password@localhost/test_db",
    )
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("PROJECT_PATH", "/tmp/test-project")

    settings = AuthSettings()

    assert settings.app_env == "test"
    assert settings.api_token.get_secret_value() == "test-api-token"
    assert settings.gemini_api_key.get_secret_value() == "test-gemini-key"
    assert (
        settings.database_url.get_secret_value()
        == "postgresql+asyncpg://user:password@localhost/test_db"
    )
    assert settings.debug is False
    assert settings.project_path == Path("/tmp/test-project")


@pytest.mark.parametrize("environment", ["development", "test", "production"])
def test_auth_settings_accepts_supported_environments(
    monkeypatch: pytest.MonkeyPatch,
    environment: str,
) -> None:
    monkeypatch.setenv("APP_ENV", environment)
    monkeypatch.setenv("API_TOKEN", "test-api-token")
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://user:password@localhost/test_db",
    )
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("PROJECT_PATH", "/tmp/test-project")

    settings = AuthSettings()

    assert settings.app_env == environment


def test_auth_settings_rejects_unknown_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.setenv("API_TOKEN", "test-api-token")
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://user:password@localhost/test_db",
    )
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("PROJECT_PATH", "/tmp/test-project")

    with pytest.raises(ValidationError):
        AuthSettings()


def test_workflow_settings_are_immutable() -> None:
    settings = WorkflowSettings()

    with pytest.raises(ValidationError):
        settings.workflow_max_rounds = settings.workflow_max_rounds + 1
