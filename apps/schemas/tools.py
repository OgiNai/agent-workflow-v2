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


class TestRunResult(BaseModel):
    status: Literal["passed", "failed", "error", "timeout"]
    tests_total: int | None = None
    tests_passed: int | None = None
    tests_failed: int | None = None
    duration_ms: int
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
