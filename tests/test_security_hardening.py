"""Security regression tests for request validation, paths, and code execution."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from apps.core.constants import (
    MAX_FILE_PATH_LENGTH,
    MAX_INLINE_CODE_LENGTH,
    MAX_INSTRUCTION_LENGTH,
)
from apps.schemas.requests import ReviewRequest
from apps.tools.file_path_helpers import resolve_project_file_path
from apps.tools.test_runner import run_pytest_for_code


def test_review_request_rejects_oversized_instruction() -> None:
    with pytest.raises(ValidationError):
        ReviewRequest(
            instruction="x" * (MAX_INSTRUCTION_LENGTH + 1),
        )


def test_review_request_rejects_oversized_inline_code() -> None:
    with pytest.raises(ValidationError):
        ReviewRequest(
            instruction="Review the code.",
            code="x" * (MAX_INLINE_CODE_LENGTH + 1),
        )


def test_review_request_rejects_oversized_file_path() -> None:
    with pytest.raises(ValidationError):
        ReviewRequest(
            instruction="Review the file.",
            file_path="a" * (MAX_FILE_PATH_LENGTH + 1),
        )


def test_resolve_project_file_path_rejects_parent_traversal(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        "apps.tools.file_path_helpers.get_project_root",
        lambda: tmp_path,
    )

    with pytest.raises(ValueError, match="Path escapes"):
        resolve_project_file_path("../outside.py")


def test_resolve_project_file_path_rejects_symlink_escape(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "project"
    outside_root = tmp_path / "outside"

    project_root.mkdir()
    outside_root.mkdir()

    outside_file = outside_root / "secret.py"
    outside_file.write_text("SECRET = True\n", encoding="utf-8")

    link = project_root / "linked.py"

    try:
        link.symlink_to(outside_file)
    except OSError as exc:
        pytest.skip(f"Symlinks are not supported in this test environment: {exc}")

    monkeypatch.setattr(
        "apps.tools.file_path_helpers.get_project_root",
        lambda: project_root,
    )

    with pytest.raises(ValueError, match="Path escapes"):
        resolve_project_file_path("linked.py")


@pytest.mark.anyio
async def test_run_pytest_for_code_does_not_inherit_application_secrets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret_name = "AGENT_WORKFLOW_TEST_SECRET"
    secret_value = "super-secret-test-value"

    monkeypatch.setenv(secret_name, secret_value)

    code = f"""
import os

SECRET_PRESENT = os.environ.get({secret_name!r}) is not None
"""

    tests = """
from solution import SECRET_PRESENT


def test_application_secret_is_not_available():
    assert SECRET_PRESENT is False
"""

    result = await run_pytest_for_code(code, tests)

    assert result.status == "passed"
    assert result.exit_code == 0
    assert secret_value not in result.stdout
    assert secret_value not in result.stderr


@pytest.mark.anyio
async def test_run_pytest_for_code_preserves_timeout_boundary() -> None:
    code = """
def infinite_loop():
    while True:
        pass
"""

    tests = """
from solution import infinite_loop


def test_infinite_loop():
    infinite_loop()
"""

    result = await run_pytest_for_code(
        code,
        tests,
        timeout_seconds=1,
    )

    assert result.status == "timeout"
    assert result.tests == []
