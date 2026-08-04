from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# easiest way to retrieve the API token is to load the environment variables
# from .env file into the environment os.environ and get it from there
# import os
# from dotenv import load_dotenv
# load_dotenv()
# API_TOKEN = os.environ.get('API_TOKEN')

# a bit more secure way to access the API token, suitable for larger number of variables
# is to use SettingsConfigDict of the BaseSettings class to automatically map environment
# variables to BaseSettings' fields if names match. Extra security is added by SecretStr
# which does not allow secrets to accidentally appear in logging or tracebacks

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
shared_config = SettingsConfigDict(
    env_file=ENV_FILE,
    env_file_encoding="utf-8",
    extra="ignore",
)


class AuthSettings(BaseSettings):
    api_token: SecretStr
    gemini_api_key: SecretStr
    database_url: SecretStr
    debug: bool
    project_path: Path

    model_config = shared_config


class WorkflowSettings(BaseSettings):
    workflow_max_rounds: int = 3
    # Development only
    workflow_force_retry_rounds: int = 0
    workflow_always_retry: bool = True

    model_config = shared_config


# cache AuthSettings and WorkflowSettings so it is only created once and then reused
@lru_cache
def get_auth_settings() -> AuthSettings:
    return AuthSettings()


@lru_cache
def get_workflow_settings() -> WorkflowSettings:
    return WorkflowSettings()
