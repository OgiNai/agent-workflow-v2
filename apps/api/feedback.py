"""Feedback API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.core.security import verify_bearer_token
from apps.database.models import Feedback
from apps.database.session import get_db_session
from apps.repositories.feedback_repository import FeedbackRepository
from apps.repositories.workflow_repository import WorkflowRepository
from apps.schemas.requests import FeedbackRequest
from apps.schemas.responses import FeedbackResponse

router = APIRouter()

BearerToken = Annotated[None, Depends(verify_bearer_token)]
DbSession = Annotated[AsyncSession, Depends(get_db_session)]


@router.post(
    "/reviews/{workflow_run_id}/feedback",
    response_model=FeedbackResponse,
    status_code=status.HTTP_200_OK,
)
async def create_feedback(
    workflow_run_id: UUID,
    feedback: FeedbackRequest,
    _: BearerToken,
    session: DbSession,
) -> FeedbackResponse:
    """Create or replace human feedback for a workflow run."""
    workflow_repository = WorkflowRepository(session)
    feedback_repository = FeedbackRepository(session)

    workflow = await workflow_repository.get(workflow_run_id)

    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow run '{workflow_run_id}' not found.",
        )

    existing_feedback = await feedback_repository.get_by_workflow(
        workflow_run_id,
    )

    if existing_feedback is None:
        feedback_record = Feedback(
            workflow_id=workflow_run_id,
            rating=feedback.rating,
            accepted=feedback.accepted,
            comments=feedback.comment,
        )
        await feedback_repository.create(feedback_record)
    else:
        existing_feedback.rating = feedback.rating
        existing_feedback.accepted = feedback.accepted
        existing_feedback.comments = feedback.comment

        feedback_record = await feedback_repository.update(
            existing_feedback,
        )

    await session.commit()

    return FeedbackResponse(
        id=feedback_record.id,
        workflow_run_id=feedback_record.workflow_id,
        rating=feedback_record.rating,
        accepted=feedback_record.accepted,
        comment=feedback_record.comments,
    )
