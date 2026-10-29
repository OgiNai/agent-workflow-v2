from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from apps.integrations.github.models import (
    GitHubChangedFile,
    GitHubFileContent,
    GitHubPullRequest,
    GitHubRepository,
)
from apps.integrations.github.service import GitHubPRReviewService
from apps.schemas.agent_outputs import EvaluatorOutput, Finding, FindingLocation
from apps.schemas.requests import ReviewRequest
from apps.schemas.responses import ReviewResponse


@pytest.fixture
def repository() -> GitHubRepository:
    return GitHubRepository(
        owner="example",
        name="project",
        default_branch="main",
    )


@pytest.fixture
def pull_request(repository: GitHubRepository) -> GitHubPullRequest:
    return GitHubPullRequest(
        number=42,
        title="Improve example implementation",
        body="Please review these changes.",
        base_ref="main",
        head_ref="feature/example",
        base_sha="base-sha",
        head_sha="head-sha",
        repository=repository,
    )


@pytest.fixture
def github_client() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def service(
    github_client: AsyncMock,
) -> GitHubPRReviewService:
    return GitHubPRReviewService(
        github_client,
        workflow_runner=AsyncMock(),
    )


def make_changed_file(
    path: str,
    *,
    status: str = "modified",
    patch: str | None = None,
) -> GitHubChangedFile:
    return GitHubChangedFile(
        path=path,
        status=status,
        additions=1,
        deletions=0,
        changes=1,
        patch=patch,
    )


def make_workflow_response(
    *,
    workflow_run_id=None,
    status: str = "completed",
    findings: list[Finding] | None = None,
) -> ReviewResponse:
    return ReviewResponse(
        workflow_run_id=workflow_run_id or uuid4(),
        status=status,
        task_type="review_refactor",
        source_type="inline",
        final_decision="pass" if status == "completed" else "failed",
        summary=f"Workflow {status}.",
        evaluation=(
            EvaluatorOutput(
                final_decision="pass",
                rule_score=1.0,
                execution_score=1.0,
                security_score=1.0,
                maintainability_score=1.0,
                correctness_score=1.0,
                findings=findings or [],
            )
            if status == "completed"
            else None
        ),
        rounds_executed=1,
    )


@pytest.mark.anyio
async def test_review_pull_request_runs_workflow_for_each_supported_file(
    github_client: AsyncMock,
    service: GitHubPRReviewService,
    pull_request: GitHubPullRequest,
) -> None:
    first_file = make_changed_file(
        "apps/first.py",
        patch="@@ -1 +1 @@\n-old\n+new\n",
    )
    second_file = make_changed_file(
        "apps/second.py",
        patch="@@ -1 +1 @@\n-old\n+new\n",
    )
    github_client.get_repository.return_value = pull_request.repository
    github_client.get_pull_request.return_value = pull_request
    github_client.list_pull_request_files.return_value = [
        first_file,
        second_file,
    ]
    github_client.get_file_content.side_effect = [
        GitHubFileContent(
            path=first_file.path,
            content="first_code = True",
            ref=pull_request.head_sha,
            sha="first-sha",
        ),
        GitHubFileContent(
            path=second_file.path,
            content="second_code = True",
            ref=pull_request.head_sha,
            sha="second-sha",
        ),
    ]

    first_response = make_workflow_response()
    second_response = make_workflow_response()
    runner = service.workflow_runner
    runner.side_effect = [first_response, second_response]

    result = await service.review_pull_request(
        owner="example",
        repository_name="project",
        pull_request_number=42,
    )

    assert result.status == "completed"
    assert [workflow.path for workflow in result.workflows] == [
        "apps/first.py",
        "apps/second.py",
    ]
    assert [workflow.workflow_run_id for workflow in result.workflows] == [
        first_response.workflow_run_id,
        second_response.workflow_run_id,
    ]

    assert runner.await_count == 2
    first_request = runner.await_args_list[0].args[0]
    second_request = runner.await_args_list[1].args[0]

    assert isinstance(first_request, ReviewRequest)
    assert isinstance(second_request, ReviewRequest)
    assert first_request.code == "first_code = True"
    assert second_request.code == "second_code = True"
    assert first_request.review_context is second_request.review_context

    github_client.create_pull_request_review.assert_not_awaited()


@pytest.mark.anyio
async def test_review_pull_request_aggregates_findings_into_one_review(
    github_client: AsyncMock,
    service: GitHubPRReviewService,
    pull_request: GitHubPullRequest,
) -> None:
    first_file = make_changed_file(
        "apps/first.py",
        patch="@@ -1 +1 @@\n-old\n+new\n",
    )
    second_file = make_changed_file(
        "apps/second.py",
        patch="@@ -1 +1 @@\n-old\n+new\n",
    )
    github_client.get_repository.return_value = pull_request.repository
    github_client.get_pull_request.return_value = pull_request
    github_client.list_pull_request_files.return_value = [
        first_file,
        second_file,
    ]
    github_client.get_file_content.side_effect = [
        GitHubFileContent(
            path=first_file.path,
            content="first_code = True",
            ref=pull_request.head_sha,
            sha="first-sha",
        ),
        GitHubFileContent(
            path=second_file.path,
            content="second_code = True",
            ref=pull_request.head_sha,
            sha="second-sha",
        ),
    ]

    first_finding = Finding(
        id="finding-1",
        category="correctness",
        severity="HIGH",
        description="First file has a correctness issue.",
        location=FindingLocation(line=1),
    )
    second_finding = Finding(
        id="finding-2",
        category="security",
        severity="CRITICAL",
        description="Second file has a security issue.",
        location=FindingLocation(line=1),
    )

    service.workflow_runner.side_effect = [
        make_workflow_response(findings=[first_finding]),
        make_workflow_response(findings=[second_finding]),
    ]
    github_client.create_pull_request_review.return_value = 123

    result = await service.review_pull_request(
        owner="example",
        repository_name="project",
        pull_request_number=42,
    )

    assert result.status == "completed"
    assert result.github_review_id == 123
    assert len(result.workflows) == 2

    github_client.create_pull_request_review.assert_awaited_once()
    review_kwargs = github_client.create_pull_request_review.await_args.kwargs

    assert review_kwargs["commit_id"] == pull_request.head_sha
    comments = review_kwargs["comments"]
    assert len(comments) == 2
    assert {comment.path for comment in comments} == {
        first_file.path,
        second_file.path,
    }
    assert "finding-1" in "\n".join(comment.body for comment in comments)
    assert "finding-2" in "\n".join(comment.body for comment in comments)


@pytest.mark.anyio
async def test_failed_workflow_prevents_partial_review_publication(
    github_client: AsyncMock,
    service: GitHubPRReviewService,
    pull_request: GitHubPullRequest,
) -> None:
    changed_file = make_changed_file("apps/example.py")
    github_client.get_repository.return_value = pull_request.repository
    github_client.get_pull_request.return_value = pull_request
    github_client.list_pull_request_files.return_value = [changed_file]
    github_client.get_file_content.return_value = GitHubFileContent(
        path=changed_file.path,
        content="example = True",
        ref=pull_request.head_sha,
        sha="file-sha",
    )
    service.workflow_runner.return_value = make_workflow_response(
        status="failed",
    )

    result = await service.review_pull_request(
        owner="example",
        repository_name="project",
        pull_request_number=42,
    )

    assert result.status == "failed"
    assert len(result.workflows) == 1
    assert result.workflows[0].status == "failed"
    assert result.github_review_id is None
    github_client.create_pull_request_review.assert_not_awaited()


@pytest.mark.anyio
async def test_no_unresolved_findings_does_not_publish_review(
    github_client: AsyncMock,
    service: GitHubPRReviewService,
    pull_request: GitHubPullRequest,
) -> None:
    changed_file = make_changed_file("apps/example.py")
    github_client.get_repository.return_value = pull_request.repository
    github_client.get_pull_request.return_value = pull_request
    github_client.list_pull_request_files.return_value = [changed_file]
    github_client.get_file_content.return_value = GitHubFileContent(
        path=changed_file.path,
        content="example = True",
        ref=pull_request.head_sha,
        sha="file-sha",
    )
    service.workflow_runner.return_value = make_workflow_response(
        findings=[
            Finding(
                id="finding-resolved",
                category="correctness",
                severity="LOW",
                description="This issue has been fixed.",
                status="resolved",
                location=FindingLocation(line=1),
            )
        ],
    )

    result = await service.review_pull_request(
        owner="example",
        repository_name="project",
        pull_request_number=42,
    )

    assert result.status == "completed"
    assert result.github_review_id is None
    github_client.create_pull_request_review.assert_not_awaited()


@pytest.mark.anyio
async def test_no_supported_files_skips_workflows_and_review_publication(
    github_client: AsyncMock,
    service: GitHubPRReviewService,
    pull_request: GitHubPullRequest,
) -> None:
    github_client.get_repository.return_value = pull_request.repository
    github_client.get_pull_request.return_value = pull_request
    github_client.list_pull_request_files.return_value = [
        make_changed_file("apps/deleted.py", status="deleted"),
        make_changed_file("assets/logo.png"),
    ]

    result = await service.review_pull_request(
        owner="example",
        repository_name="project",
        pull_request_number=42,
    )

    assert result.status == "completed"
    assert result.workflows == []
    assert result.github_review_id is None
    service.workflow_runner.assert_not_awaited()
    github_client.get_file_content.assert_not_awaited()
    github_client.create_pull_request_review.assert_not_awaited()
