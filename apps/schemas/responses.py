"""API response schemas."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from apps.schemas.agent_outputs import EvaluatorOutput
from apps.schemas.workflow import ArtifactInfo, WorkflowStepTrace


class ReviewResponse(BaseModel):
    """Unified response for the /reviews endpoint."""

    workflow_run_id: UUID
    status: str
    task_type: str
    source_type: str
    final_decision: str
    summary: str
    final_code: str | None = None
    evaluation: EvaluatorOutput | None = None
    artifacts: list[ArtifactInfo] = Field(default_factory=list)
    rounds_executed: int
    steps: list[WorkflowStepTrace] = Field(default_factory=list)


class FeedbackResponse(BaseModel):
    """Response for workflow feedback."""

    id: UUID
    workflow_run_id: UUID
    rating: int
    accepted: bool
    comment: str | None = None


class GitHubFileWorkflowResult(BaseModel):
    """Outcome of reviewing one changed file in a pull request."""

    path: str
    workflow_run_id: UUID
    status: str
    final_decision: str
    summary: str


class GitHubPullRequestReviewResponse(BaseModel):
    """Aggregate outcome of reviewing a GitHub pull request."""

    repository: str
    pull_request_number: int
    head_sha: str
    status: Literal["completed", "failed"]
    workflows: list[GitHubFileWorkflowResult] = Field(default_factory=list)
    github_review_id: int | None = None
