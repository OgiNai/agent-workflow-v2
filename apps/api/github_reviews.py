"""GitHub pull-request review API endpoint."""

from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from apps.core.security import verify_bearer_token
from apps.integrations.github.client import GitHubRESTClient
from apps.integrations.github.errors import GitHubIntegrationError
from apps.integrations.github.service import GitHubPRReviewService
from apps.schemas.responses import GitHubPullRequestReviewResponse

router = APIRouter()


@router.post(
    "/github/repositories/{owner}/{repository_name}"
    "/pull-requests/{pull_request_number}/review",
    response_model=GitHubPullRequestReviewResponse,
    status_code=HTTPStatus.ACCEPTED,
    tags=["github-reviews"],
)
async def create_github_pull_request_review(
    owner: str,
    repository_name: str,
    pull_request_number: int,
    _: None = Depends(verify_bearer_token),
) -> GitHubPullRequestReviewResponse | JSONResponse:
    """Review a pull request and publish one aggregate GitHub review."""
    if pull_request_number < 1:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="pull_request_number must be positive.",
        )

    try:
        async with GitHubRESTClient() as client:
            result = await GitHubPRReviewService(
                client,
            ).review_pull_request(
                owner=owner,
                repository_name=repository_name,
                pull_request_number=pull_request_number,
            )
    except GitHubIntegrationError as exc:
        raise HTTPException(
            status_code=HTTPStatus.BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    if result.status == "failed":
        return JSONResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            content=result.model_dump(mode="json"),
        )

    return result
