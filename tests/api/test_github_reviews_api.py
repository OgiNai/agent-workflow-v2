from collections.abc import Iterator
from typing import Self
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from apps.core.security import verify_bearer_token
from apps.integrations.github.errors import GitHubAPIError
from apps.integrations.github.service import GitHubPRReviewService
from apps.main import code_app
from apps.schemas.responses import (
    GitHubFileWorkflowResult,
    GitHubPullRequestReviewResponse,
)

ENDPOINT = "/github/repositories/example/project/pull-requests/42/review"


@pytest.fixture
def authenticated_client() -> Iterator[TestClient]:
    async def bypass_auth() -> None:
        return None

    code_app.dependency_overrides[verify_bearer_token] = bypass_auth

    try:
        with TestClient(code_app) as client:
            yield client
    finally:
        code_app.dependency_overrides.pop(verify_bearer_token, None)


@pytest.fixture
def review_response() -> GitHubPullRequestReviewResponse:
    return GitHubPullRequestReviewResponse(
        repository="example/project",
        pull_request_number=42,
        head_sha="head-sha",
        status="completed",
        workflows=[
            GitHubFileWorkflowResult(
                path="apps/example.py",
                workflow_run_id=uuid4(),
                status="completed",
                final_decision="pass_with_warnings",
                summary="Review completed.",
            )
        ],
        github_review_id=123,
    )


class FakeGitHubClient:
    """Minimal async context manager used by the API tests."""

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_args: object) -> None:
        return None


def install_service_mock(
    monkeypatch: pytest.MonkeyPatch,
    result: GitHubPullRequestReviewResponse | None = None,
    *,
    error: Exception | None = None,
) -> AsyncMock:
    client = FakeGitHubClient()
    service = AsyncMock(spec=GitHubPRReviewService)

    if error is not None:
        service.review_pull_request.side_effect = error
    else:
        assert result is not None
        service.review_pull_request.return_value = result

    monkeypatch.setattr(
        "apps.api.github_reviews.GitHubRESTClient",
        lambda: client,
    )
    monkeypatch.setattr(
        "apps.api.github_reviews.GitHubPRReviewService",
        lambda _client: service,
    )

    return service


def test_create_github_review_returns_aggregate_response(
    authenticated_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    review_response: GitHubPullRequestReviewResponse,
) -> None:
    service = install_service_mock(
        monkeypatch,
        result=review_response,
    )

    response = authenticated_client.post(ENDPOINT)

    assert response.status_code == 202
    assert response.json()["repository"] == "example/project"
    assert response.json()["pull_request_number"] == 42
    assert response.json()["head_sha"] == "head-sha"
    assert response.json()["status"] == "completed"
    assert response.json()["github_review_id"] == 123
    assert response.json()["workflows"][0]["path"] == "apps/example.py"

    service.review_pull_request.assert_awaited_once_with(
        owner="example",
        repository_name="project",
        pull_request_number=42,
    )


def test_create_github_review_maps_integration_errors_to_502(
    authenticated_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_service_mock(
        monkeypatch,
        error=GitHubAPIError("GitHub API request failed."),
    )

    response = authenticated_client.post(ENDPOINT)

    assert response.status_code == 502
    assert response.json()["detail"] == "GitHub API request failed."


def test_create_github_review_returns_500_for_failed_workflow(
    authenticated_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failed_response = GitHubPullRequestReviewResponse(
        repository="example/project",
        pull_request_number=42,
        head_sha="head-sha",
        status="failed",
        workflows=[
            GitHubFileWorkflowResult(
                path="apps/example.py",
                workflow_run_id=uuid4(),
                status="failed",
                final_decision="failed",
                summary="Workflow failed.",
            )
        ],
        github_review_id=None,
    )
    install_service_mock(
        monkeypatch,
        result=failed_response,
    )

    response = authenticated_client.post(ENDPOINT)

    assert response.status_code == 500
    assert response.json()["status"] == "failed"
    assert response.json()["github_review_id"] is None


def test_create_github_review_rejects_non_positive_pr_number(
    authenticated_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = install_service_mock(
        monkeypatch,
        result=GitHubPullRequestReviewResponse(
            repository="example/project",
            pull_request_number=0,
            head_sha="head-sha",
            status="completed",
        ),
    )

    response = authenticated_client.post(
        "/github/repositories/example/project/pull-requests/0/review"
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "pull_request_number must be positive."
    service.review_pull_request.assert_not_awaited()


def test_create_github_review_requires_authentication() -> None:
    # Avoid entering the application lifespan; this request should be rejected
    # by HTTPBearer before any GitHub client or workflow is constructed.
    with TestClient(code_app) as client:
        response = client.post(ENDPOINT)

    assert response.status_code in {401, 403}
