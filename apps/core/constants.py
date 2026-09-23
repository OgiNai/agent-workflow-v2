"""Shared constants for the workflow MVP."""

from typing import Final

ALLOWED_READ_EXTENSIONS: Final[frozenset[str]] = {
    ".py",
    ".txt",
    ".md",
    ".json",
    ".yaml",
    ".yml",
}
ALLOWED_WRITE_EXTENSIONS: Final[frozenset[str]] = {".py", ".txt", ".md", ".json"}
MAX_FILE_SIZE_BYTES: Final[int] = 200_000

MAX_INSTRUCTION_LENGTH: Final[int] = 10_000
MAX_INLINE_CODE_LENGTH: Final[int] = 200_000
MAX_FILE_PATH_LENGTH: Final[int] = 4_096

# workflow
DEFAULT_MAX_ROUNDS: Final[int] = 2
MAX_ROUNDS_LIMIT: Final[int] = 5
WORKSPACE_DIR_NAME: Final[str] = "workspace"
REVIEW_RUNS_DIR_NAME: Final[str] = "review_runs"

TASK_TYPES: Final[tuple[str, ...]] = (
    "auto",
    "generate",
    "review",
    "refactor",
    "review_refactor",
)
INPUT_TYPES: Final[tuple[str, ...]] = (
    "auto",
    "inline_code",
    "file_path",
    "natural_language",
)

# Gemini
GEMINI_INITIAL_DELAY_SECONDS = 5
GEMINI_MAX_ATTEMPTS = 3

# LLM
DEFAULT_LLM_TEMPERATURE = 0.2

# GitHub
GITHUB_API_BASE_URL = "https://api.github.com"
GITHUB_API_VERSION = "2026-03-10"
GITHUB_ACCEPT_HEADER = "application/vnd.github+json"
DEFAULT_TIMEOUT_SECONDS = 30.0
PER_PAGE = 100
