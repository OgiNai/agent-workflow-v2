"""Internal workflow state schemas."""

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

ResolvedTaskType = Literal["generate", "review_refactor"]
SourceType = Literal["none", "inline_code", "file_path"]


class RouterResult(BaseModel):
    """Normalized result produced by the deterministic input router."""

    task_type: ResolvedTaskType
    source_type: SourceType
    instruction: str
    code_available: bool
    code: str | None = None
    source_path: str | None = None
    #original_content: str | None = None


class WorkflowPlan(BaseModel):
    """Plan for the orchestrator."""

    task_type: ResolvedTaskType
    requires_generation: bool
    requires_refactor: bool = True
    requires_tests: bool = True
    max_rounds: int
    steps: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class CandidateCode(BaseModel):
    """Current code candidate moving through the workflow."""

    code: str
    origin: str
    round_number: int = 0


class WorkflowStepTrace(BaseModel):
    """In-memory trace for Milestone 1. This maps to agent_steps/tool_calls later."""

    step_name: str
    step_type: Literal["agent", "tool", "workflow", "evaluation"]
    status: Literal["success", "failed", "skipped"]
    latency_ms: int | None = None
    round_number: int | None = None
    detail: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ArtifactInfo(BaseModel):
    """Saved artifact metadata."""

    artifact_type: str
    path: str
    size_bytes: int | None = None
    content_hash: str | None = None


class WorkflowContext(BaseModel):
    """Mutable context passed between workflow steps."""

    workflow_run_id: UUID
    request_id: str
    traces: list[WorkflowStepTrace] = Field(default_factory=list)
    artifacts: list[ArtifactInfo] = Field(default_factory=list)
