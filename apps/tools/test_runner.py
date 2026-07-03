"""Deterministic pytest runner tool."""

import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Literal

from pydantic import BaseModel


class TestRunResult(BaseModel):
    status: Literal["passed", "failed", "error", "timeout"]
    tests_total: int | None = None
    tests_passed: int | None = None
    tests_failed: int | None = None
    duration_ms: int
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""


def run_pytest_for_code(code: str, tests: str, timeout_seconds: int = 10) -> TestRunResult:
    """Run generated pytest tests against candidate code in a temporary directory."""
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="agent_review_tests_") as temp_dir:
        temp_path = Path(temp_dir)
        (temp_path / "solution.py").write_text(code, encoding="utf-8")
        (temp_path / "test_solution.py").write_text(tests, encoding="utf-8")
        try:
            completed = subprocess.run(
                [sys.executable, "-m", "pytest", "test_solution.py", "-q"],
                cwd=temp_path,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return TestRunResult(
                status="timeout",
                duration_ms=int((time.perf_counter() - started) * 1000),
                stdout=exc.stdout or "",
                stderr=exc.stderr or "",
            )
        except Exception as exc:
            return TestRunResult(
                status="error",
                duration_ms=int((time.perf_counter() - started) * 1000),
                stderr=str(exc),
            )

    status: Literal["passed", "failed"] = "passed" if completed.returncode == 0 else "failed"
    return TestRunResult(
        status=status,
        duration_ms=int((time.perf_counter() - started) * 1000),
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
