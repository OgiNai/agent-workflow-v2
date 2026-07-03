"""Shared constants for the workflow MVP."""

from typing import Final

ALLOWED_READ_EXTENSIONS: Final[set[str]] = {".py", ".txt", ".md", ".json", ".yaml", ".yml"}
ALLOWED_WRITE_EXTENSIONS: Final[set[str]] = {".py", ".txt", ".md", ".json"}
MAX_FILE_SIZE_BYTES: Final[int] = 200_000
DEFAULT_MAX_ROUNDS: Final[int] = 2
MAX_ROUNDS_LIMIT: Final[int] = 5
WORKSPACE_DIR_NAME: Final[str] = "workspace"
REVIEW_RUNS_DIR_NAME: Final[str] = "review_runs"

TASK_TYPES: Final[tuple[str, ...]] = ("auto", "generate", "review", "refactor", "review_refactor")
INPUT_TYPES: Final[tuple[str, ...]] = ("auto", "inline_code", "file_path", "natural_language")
