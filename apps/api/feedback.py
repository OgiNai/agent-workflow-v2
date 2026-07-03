"""Feedback endpoints placeholder for Milestone 2 persistence."""

from fastapi import APIRouter, Depends

from apps.core.security import verify_bearer_token
from apps.schemas.requests import FeedbackRequest

router = APIRouter()


@router.post("/reviews/{workflow_run_id}/feedback")
async def create_feedback(
    workflow_run_id: str,
    feedback: FeedbackRequest,
    _: None = Depends(verify_bearer_token),
):
    """Accept feedback payload; persistence will be added with Neon in Milestone 2."""
    return {
        "workflow_run_id": workflow_run_id,
        "status": "accepted_not_persisted_yet",
        "feedback": feedback.model_dump(),
    }
