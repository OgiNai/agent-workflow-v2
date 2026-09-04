"""Shared tool result schemas."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    tool_name: str
    status: Literal["success", "failed"]
    output: str | None = None
    error: str | None = None
    latency_ms: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TestCaseResult(BaseModel):
    """Structured result for an individual candidate test."""

    nodeid: str
    outcome: Literal[
        "passed",
        "failed",
        "skipped",
        "xfailed",
        "xpassed",
    ]
    duration_ms: int | None = None
    failure_message: str | None = None
    traceback: str | None = None


class TestRunResult(BaseModel):
    """Structured result of executing generated candidate tests."""

    # Prevent pytest from treating this Pydantic model as a test class.
    __test__ = False

    status: Literal["passed", "failed", "error", "timeout"]

    tests_total: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    tests_skipped: int = 0
    tests_xfailed: int = 0
    tests_xpassed: int = 0

    duration_ms: int
    exit_code: int | None = None

    tests: list[TestCaseResult] = Field(default_factory=list)

    stdout: str = ""
    stderr: str = ""
