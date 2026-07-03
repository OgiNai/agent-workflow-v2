"""API response schemas."""

from uuid import UUID

from pydantic import BaseModel, Field

from apps.schemas.agent_outputs import EvaluatorOutput
from apps.schemas.workflow import ArtifactInfo, WorkflowStepTrace


class ReviewResponse(BaseModel):
    """Unified response for the /reviews endpoint."""

    workflow_run_id: UUID
    status: str
    task_type: str
    input_type: str
    final_decision: str
    summary: str
    final_code: str | None = None
    evaluation: EvaluatorOutput | None = None
    artifacts: list[ArtifactInfo] = Field(default_factory=list)
    rounds_executed: int
    steps: list[WorkflowStepTrace] = Field(default_factory=list)
