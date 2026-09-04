"""Parser for structured pytest-json-report output."""

from typing import Any

from apps.schemas.tools import TestCaseResult, TestRunResult

_SUPPORTED_OUTCOMES = {
    "passed",
    "failed",
    "skipped",
    "xfailed",
    "xpassed",
}


def parse_pytest_json_report(
    report: dict[str, Any],
    *,
    duration_ms: int,
    exit_code: int | None,
    stdout: str = "",
    stderr: str = "",
) -> TestRunResult:
    """Convert a pytest-json-report payload into a TestRunResult."""

    summary = report.get("summary")

    if not isinstance(summary, dict):
        raise TypeError("Pytest JSON report is missing a valid summary.")

    raw_tests = report.get("tests", [])

    if not isinstance(raw_tests, list):
        raise TypeError("Pytest JSON report contains an invalid tests field.")

    tests: list[TestCaseResult] = []

    for raw_test in raw_tests:
        if not isinstance(raw_test, dict):
            continue

        nodeid = raw_test.get("nodeid")
        outcome = raw_test.get("outcome")

        if not isinstance(nodeid, str):
            continue

        if outcome not in _SUPPORTED_OUTCOMES:
            # pytest-json-report can also expose "error" for setup/teardown
            # execution errors. Those are represented by the run-level status
            # and are not one of the supported individual test outcomes.
            continue

        tests.append(
            TestCaseResult(
                nodeid=nodeid,
                outcome=outcome,
                duration_ms=_extract_duration_ms(raw_test),
                failure_message=_extract_failure_message(raw_test),
                traceback=_extract_traceback(raw_test),
            )
        )

    tests_total = _summary_count(summary, "total")
    tests_passed = _summary_count(summary, "passed")
    tests_failed = _summary_count(summary, "failed")
    tests_skipped = _summary_count(summary, "skipped")
    tests_xfailed = _summary_count(summary, "xfailed")
    tests_xpassed = _summary_count(summary, "xpassed")
    execution_errors = _summary_count(summary, "error")

    status = _determine_status(
        exit_code=exit_code,
        execution_errors=execution_errors,
        tests_failed=tests_failed,
    )

    return TestRunResult(
        status=status,
        tests_total=tests_total,
        tests_passed=tests_passed,
        tests_failed=tests_failed,
        tests_skipped=tests_skipped,
        tests_xfailed=tests_xfailed,
        tests_xpassed=tests_xpassed,
        duration_ms=duration_ms,
        exit_code=exit_code,
        tests=tests,
        stdout=stdout,
        stderr=stderr,
    )


def _summary_count(summary: dict[str, Any], key: str) -> int:
    """Return a non-negative integer summary count."""

    value = summary.get(key, 0)

    if isinstance(value, bool):
        return 0

    if isinstance(value, int):
        return max(value, 0)

    return 0


def _extract_duration_ms(test: dict[str, Any]) -> int | None:
    """Sum durations of pytest setup, call, and teardown stages."""

    total_seconds = 0.0
    found_duration = False

    for stage_name in ("setup", "call", "teardown"):
        stage = test.get(stage_name)

        if not isinstance(stage, dict):
            continue

        duration = stage.get("duration")

        if isinstance(duration, (int, float)) and duration >= 0:
            total_seconds += float(duration)
            found_duration = True

    if not found_duration:
        return None

    return int(total_seconds * 1000)


def _extract_failure_message(test: dict[str, Any]) -> str | None:
    """Extract the first useful failure representation."""

    for stage_name in ("setup", "call", "teardown"):
        stage = test.get(stage_name)

        if not isinstance(stage, dict):
            continue

        longrepr = stage.get("longrepr")

        if isinstance(longrepr, str) and longrepr:
            return longrepr

        crash = stage.get("crash")

        if isinstance(crash, dict):
            message = crash.get("message")

            if isinstance(message, str) and message:
                return message

    return None


def _extract_traceback(test: dict[str, Any]) -> str | None:
    """Convert pytest-json-report traceback entries to text."""

    for stage_name in ("setup", "call", "teardown"):
        stage = test.get(stage_name)

        if not isinstance(stage, dict):
            continue

        traceback = stage.get("traceback")

        if isinstance(traceback, str) and traceback:
            return traceback

        if isinstance(traceback, list):
            lines: list[str] = []

            for entry in traceback:
                if isinstance(entry, str):
                    lines.append(entry)
                    continue

                if not isinstance(entry, dict):
                    continue

                path = entry.get("path")
                lineno = entry.get("lineno")
                message = entry.get("message")

                location = ""

                if isinstance(path, str):
                    location = path

                    if isinstance(lineno, int):
                        location = f"{location}:{lineno}"

                if isinstance(message, str) and message:
                    if location:
                        lines.append(f"{location}: {message}")
                    else:
                        lines.append(message)
                elif location:
                    lines.append(location)

            if lines:
                return "\n".join(lines)

    return None


def _determine_status(
    *,
    exit_code: int | None,
    execution_errors: int,
    tests_failed: int,
) -> str:
    """Determine the application-level execution status."""

    if execution_errors > 0:
        return "failed"

    if tests_failed > 0:
        return "failed"

    if exit_code is not None and exit_code != 0:
        return "failed"

    return "passed"
