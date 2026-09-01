"""Deterministic pytest runner tool."""

import asyncio
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Literal

from opentelemetry.trace import SpanKind, Status, StatusCode

from apps.observability.telemetry import get_tracer
from apps.schemas.tools import TestRunResult


async def run_pytest_for_code(
    code: str,
    tests: str,
    timeout_seconds: int = 10,
) -> TestRunResult:
    """Run generated pytest tests against candidate code in a temporary directory."""

    tracer = get_tracer("apps.tools")

    with tracer.start_as_current_span("tool.pytest", kind=SpanKind.INTERNAL) as span:
        started = time.perf_counter()

        span.set_attribute("tool.pytest.timeout_seconds", timeout_seconds)

        with tempfile.TemporaryDirectory(prefix="agent_review_tests_") as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "solution.py").write_text(code, encoding="utf-8")
            (temp_path / "test_solution.py").write_text(tests, encoding="utf-8")

            try:
                process = await asyncio.create_subprocess_exec(
                    sys.executable,
                    "-m",
                    "pytest",
                    "test_solution.py",
                    "-q",
                    cwd=temp_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                try:
                    stdout_bytes, stderr_bytes = await asyncio.wait_for(
                        process.communicate(),
                        timeout=timeout_seconds,
                    )
                except TimeoutError:
                    process.kill()
                    stdout_bytes, stderr_bytes = await process.communicate()

                    result = TestRunResult(
                        status="timeout",
                        duration_ms=int((time.perf_counter() - started) * 1000),
                        stdout=stdout_bytes.decode(errors="replace"),
                        stderr=stderr_bytes.decode(errors="replace"),
                    )

                    span.set_attribute("tool.pytest.status", result.status)
                    span.set_status(
                        Status(
                            StatusCode.ERROR,
                            "Pytest execution timed out.",
                        )
                    )

                    return result

            except OSError as exc:
                span.record_exception(exc)
                span.set_status(
                    Status(
                        StatusCode.ERROR,
                        str(exc),
                    )
                )

                return TestRunResult(
                    status="error",
                    duration_ms=int((time.perf_counter() - started) * 1000),
                    stderr=str(exc),
                )

        exit_code = process.returncode

        status: Literal["passed", "failed"] = "passed" if exit_code == 0 else "failed"

        stdout = stdout_bytes.decode(errors="replace")
        stderr = stderr_bytes.decode(errors="replace")

        passed = failed = 0

        if match := re.search(r"(\d+)\s+passed", stdout):
            passed = int(match.group(1))

        if match := re.search(r"(\d+)\s+failed", stdout):
            failed = int(match.group(1))

        tests_total = passed + failed if (passed or failed) else None

        result = TestRunResult(
            status=status,
            duration_ms=int((time.perf_counter() - started) * 1000),
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            tests_total=tests_total,
            tests_passed=passed,
            tests_failed=failed,
        )

        span.set_attribute("tool.pytest.status", result.status)

        if result.tests_total is not None:
            span.set_attribute("tool.pytest.tests_total", result.tests_total)

        span.set_attribute("tool.pytest.tests_passed", result.tests_passed)
        span.set_attribute("tool.pytest.tests_failed", result.tests_failed)

        if result.status == "passed":
            span.set_status(Status(StatusCode.OK))
        else:
            span.set_status(
                Status(
                    StatusCode.ERROR,
                    "Pytest reported failed tests.",
                )
            )

        return result
