"""Deterministic pytest runner tool for generated candidate tests."""

import asyncio
import json
import sys
import tempfile
import time
from pathlib import Path

from opentelemetry.trace import SpanKind, Status, StatusCode

from apps.observability.telemetry import get_tracer
from apps.schemas.tools import TestRunResult
from apps.tools.pytest_report import parse_pytest_json_report


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
            solution_path = temp_path / "solution.py"
            tests_path = temp_path / "test_solution.py"
            report_path = temp_path / "pytest-report.json"

            solution_path.write_text(code, encoding="utf-8")
            tests_path.write_text(tests, encoding="utf-8")

            try:
                process = await asyncio.create_subprocess_exec(
                    sys.executable,
                    "-m",
                    "pytest",
                    "test_solution.py",
                    "-q",
                    "--json-report",
                    f"--json-report-file={report_path}",
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

                    _record_telemetry(span, result)

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

            stdout = stdout_bytes.decode(errors="replace")
            stderr = stderr_bytes.decode(errors="replace")
            exit_code = process.returncode
            duration_ms = int((time.perf_counter() - started) * 1000)

            try:
                report = _read_json_report(report_path)
                result = parse_pytest_json_report(
                    report,
                    duration_ms=duration_ms,
                    exit_code=exit_code,
                    stdout=stdout,
                    stderr=stderr,
                )
            except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
                span.record_exception(exc)

                result = TestRunResult(
                    status="error",
                    duration_ms=duration_ms,
                    exit_code=exit_code,
                    stdout=stdout,
                    stderr=stderr,
                )

                _record_telemetry(span, result)

                span.set_status(
                    Status(
                        StatusCode.ERROR,
                        "Pytest JSON report was unavailable or invalid.",
                    )
                )

                return result

        _record_telemetry(span, result)

        if result.status == "passed":
            span.set_status(Status(StatusCode.OK))
        elif result.status == "failed":
            span.set_status(
                Status(
                    StatusCode.ERROR,
                    "Pytest reported failed tests.",
                )
            )
        else:
            span.set_status(
                Status(
                    StatusCode.ERROR,
                    f"Pytest execution ended with status '{result.status}'.",
                )
            )

        return result


def _read_json_report(report_path: Path) -> dict:
    """Read and validate the generated pytest JSON report."""

    report_text = report_path.read_text(encoding="utf-8")
    report = json.loads(report_text)

    if not isinstance(report, dict):
        raise TypeError("Pytest JSON report must contain a JSON object.")

    return report


def _record_telemetry(span, result: TestRunResult) -> None:
    """Record structured candidate-test execution metrics on the span."""

    span.set_attribute("tool.pytest.status", result.status)
    span.set_attribute("tool.pytest.tests_total", result.tests_total)
    span.set_attribute("tool.pytest.tests_passed", result.tests_passed)
    span.set_attribute("tool.pytest.tests_failed", result.tests_failed)
    span.set_attribute("tool.pytest.tests_skipped", result.tests_skipped)
    span.set_attribute("tool.pytest.tests_xfailed", result.tests_xfailed)
    span.set_attribute("tool.pytest.tests_xpassed", result.tests_xpassed)
