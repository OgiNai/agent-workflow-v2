"""Unified review workflow API endpoints."""

from http import HTTPStatus

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from apps.core.security import verify_bearer_token
from apps.schemas.requests import ReviewRequest
from apps.schemas.responses import ReviewResponse
from apps.workflows.code_workflow import run_code_workflow

router = APIRouter()


@router.post("/reviews", response_model=ReviewResponse, status_code=HTTPStatus.ACCEPTED)
async def create_review(
    request_data: ReviewRequest,
    _: None = Depends(verify_bearer_token),
) -> ReviewResponse | JSONResponse:
    """Run the unified code generation/review/refactoring workflow."""
    result = await run_code_workflow(request_data)
    if result.status == "failed":
        return JSONResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, content=result.model_dump(mode="json"))
    return result
