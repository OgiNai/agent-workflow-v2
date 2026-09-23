"""Tests for the GitHub integration adapter."""

from unittest.mock import AsyncMock

import pytest

from apps.integrations.github.adapter import GitHubAdapter
from apps.integrations.github.models import (
    GitHubChangedFile,
    GitHubFileContent,
    GitHubPullRequest,
    GitHubRepository,
)
from apps.schemas.requests import ReviewRequest


@pytest.fixture
def github_client() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def adapter(github_client: AsyncMock) -> GitHubAdapter:
    return GitHubAdapter(github_client)


@pytest.fixture
def repository() -> GitHubRepository:
    return GitHubRepository(
        owner="test-owner",
        name="test-repository",
        default_branch="main",
    )


@pytest.fixture
def pull_request(repository: GitHubRepository) -> GitHubPullRequest:
    return GitHubPullRequest(
        number=42,
        title="Improve validation",
        body="Improve input validation.",
        base_ref="main",
        head_ref="feature/validation",
        base_sha="base-sha",
        head_sha="head-sha",
        repository=repository,
    )


@pytest.mark.anyio
async def test_build_review_requests_fetches_changed_files(
    adapter: GitHubAdapter,
    github_client: AsyncMock,
    pull_request: GitHubPullRequest,
) -> None:
    github_client.list_pull_request_files.return_value = []

    result = await adapter.build_review_requests(pull_request)

    assert result == []
    github_client.list_pull_request_files.assert_awaited_once_with(pull_request)
    github_client.get_file_content.assert_not_awaited()


@pytest.mark.anyio
async def test_build_review_requests_skips_deleted_files(
    adapter: GitHubAdapter,
    github_client: AsyncMock,
    pull_request: GitHubPullRequest,
) -> None:
    deleted_file = GitHubChangedFile(
        path="src/removed.py",
        status="deleted",
        additions=0,
        deletions=20,
        changes=20,
        patch=None,
    )
    github_client.list_pull_request_files.return_value = [deleted_file]

    result = await adapter.build_review_requests(pull_request)

    assert result == []
    github_client.get_file_content.assert_not_awaited()


@pytest.mark.anyio
async def test_build_review_requests_skips_unsupported_file_types(
    adapter: GitHubAdapter,
    github_client: AsyncMock,
    pull_request: GitHubPullRequest,
) -> None:
    unsupported_file = GitHubChangedFile(
        path="assets/logo.png",
        status="modified",
        additions=1,
        deletions=1,
        changes=2,
        patch=None,
    )
    github_client.list_pull_request_files.return_value = [unsupported_file]

    result = await adapter.build_review_requests(pull_request)

    assert result == []
    github_client.get_file_content.assert_not_awaited()


@pytest.mark.anyio
async def test_build_review_requests_fetches_supported_files_at_head_sha(
    adapter: GitHubAdapter,
    github_client: AsyncMock,
    pull_request: GitHubPullRequest,
) -> None:
    changed_file = GitHubChangedFile(
        path="apps/example.py",
        status="modified",
        additions=3,
        deletions=1,
        changes=4,
        patch="@@ -1 +1 @@",
    )
    file_content = GitHubFileContent(
        path="apps/example.py",
        content="print('updated')",
        ref=pull_request.head_sha,
        sha="file-sha",
    )

    github_client.list_pull_request_files.return_value = [changed_file]
    github_client.get_file_content.return_value = file_content

    result = await adapter.build_review_requests(pull_request)

    assert len(result) == 1
    assert isinstance(result[0], ReviewRequest)
    assert result[0].code == file_content.content

    github_client.get_file_content.assert_awaited_once_with(
        repository=pull_request.repository,
        path=changed_file.path,
        ref=pull_request.head_sha,
    )


@pytest.mark.anyio
async def test_build_review_requests_processes_multiple_supported_files(
    adapter: GitHubAdapter,
    github_client: AsyncMock,
    pull_request: GitHubPullRequest,
) -> None:
    first_file = GitHubChangedFile(
        path="apps/first.py",
        status="modified",
        additions=2,
        deletions=1,
        changes=3,
        patch="@@ -1 +1 @@",
    )
    second_file = GitHubChangedFile(
        path="apps/second.py",
        status="added",
        additions=5,
        deletions=0,
        changes=5,
        patch="@@ -0,0 +1 @@",
    )

    first_content = GitHubFileContent(
        path=first_file.path,
        content="print('first')",
        ref=pull_request.head_sha,
        sha="first-sha",
    )
    second_content = GitHubFileContent(
        path=second_file.path,
        content="print('second')",
        ref=pull_request.head_sha,
        sha="second-sha",
    )

    github_client.list_pull_request_files.return_value = [
        first_file,
        second_file,
    ]
    github_client.get_file_content.side_effect = [
        first_content,
        second_content,
    ]

    result = await adapter.build_review_requests(pull_request)

    assert len(result) == 2
    assert [request.code for request in result] == [
        first_content.content,
        second_content.content,
    ]

    assert github_client.get_file_content.await_args_list == [
        (
            (),
            {
                "repository": pull_request.repository,
                "path": first_file.path,
                "ref": pull_request.head_sha,
            },
        ),
        (
            (),
            {
                "repository": pull_request.repository,
                "path": second_file.path,
                "ref": pull_request.head_sha,
            },
        ),
    ]


@pytest.mark.anyio
async def test_build_review_requests_filters_before_fetching_content(
    adapter: GitHubAdapter,
    github_client: AsyncMock,
    pull_request: GitHubPullRequest,
) -> None:
    supported_file = GitHubChangedFile(
        path="apps/example.py",
        status="modified",
        additions=2,
        deletions=1,
        changes=3,
        patch="@@ -1 +1 @@",
    )
    deleted_file = GitHubChangedFile(
        path="apps/deleted.py",
        status="deleted",
        additions=0,
        deletions=10,
        changes=10,
        patch=None,
    )
    unsupported_file = GitHubChangedFile(
        path="assets/logo.png",
        status="modified",
        additions=1,
        deletions=1,
        changes=2,
        patch=None,
    )

    github_client.list_pull_request_files.return_value = [
        supported_file,
        deleted_file,
        unsupported_file,
    ]
    github_client.get_file_content.return_value = GitHubFileContent(
        path=supported_file.path,
        content="print('supported')",
        ref=pull_request.head_sha,
        sha="file-sha",
    )

    result = await adapter.build_review_requests(pull_request)

    assert len(result) == 1
    assert result[0].code == "print('supported')"

    github_client.get_file_content.assert_awaited_once_with(
        repository=pull_request.repository,
        path=supported_file.path,
        ref=pull_request.head_sha,
    )
