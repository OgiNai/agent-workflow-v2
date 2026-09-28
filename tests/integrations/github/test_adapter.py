"""Tests for the GitHub integration adapter."""

from unittest.mock import AsyncMock, call
from uuid import uuid4

import pytest

from apps.integrations.github.adapter import GitHubAdapter
from apps.integrations.github.models import (
    GitHubChangedFile,
    GitHubFileContent,
    GitHubPullRequest,
    GitHubRepository,
    GitHubWorkflowFindings,
)
from apps.schemas.agent_outputs import Finding, FindingLocation
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
    supported_file = GitHubChangedFile(
        path="app/gallery.py",
        status="modified",
        additions=2,
        deletions=0,
        changes=2,
        patch=None,
    )
    renamed_file = GitHubChangedFile(
        path="apps/new_name.py",
        status="renamed",
        additions=2,
        deletions=1,
        changes=3,
        previous_path="apps/old_name.py",
        patch="@@ -1 +1 @@",
    )
    supported_file_content = GitHubFileContent(
        path=supported_file.path,
        content="def gallery():\n    pass\n",
        ref=pull_request.head_sha,
        sha="file-sha",
    )
    renamed_file_content = GitHubFileContent(
        path=renamed_file.path,
        content="def name():\n    pass\n",
        ref=pull_request.head_sha,
        sha="file-sha",
    )
    github_client.list_pull_request_files.return_value = [
        unsupported_file,
        supported_file,
        renamed_file,
    ]
    github_client.get_file_content.side_effect = [
        supported_file_content,
        renamed_file_content,
    ]

    result = await adapter.build_review_requests(pull_request)

    assert len(result) == 2
    assert result[0].code == supported_file_content.content
    assert result[1].code == renamed_file_content.content

    assert github_client.get_file_content.await_count == 2
    assert github_client.get_file_content.await_args_list == [
        call(
            repository=pull_request.repository,
            path=supported_file.path,
            ref=pull_request.head_sha,
        ),
        call(
            repository=pull_request.repository,
            path=renamed_file.path,
            ref=pull_request.head_sha,
        ),
    ]

    context = result[0].review_context

    assert context is not None
    assert context.changed_files == [
        unsupported_file,
        supported_file,
        renamed_file,
    ]
    assert context.changed_files[0].path == "assets/logo.png"
    assert context.changed_files[1].path == "app/gallery.py"
    assert context.changed_files[2].previous_path == "apps/old_name.py"

    assert result[0].review_context is result[1].review_context


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
        call(
            repository=pull_request.repository,
            path=first_file.path,
            ref=pull_request.head_sha,
        ),
        call(
            repository=pull_request.repository,
            path=second_file.path,
            ref=pull_request.head_sha,
        ),
    ]

    assert result[0].review_context is result[1].review_context

    context = result[0].review_context

    assert context is not None
    assert context.pull_request_number == pull_request.number
    assert context.title == pull_request.title
    assert context.body == pull_request.body
    assert context.base_ref == pull_request.base_ref
    assert context.head_ref == pull_request.head_ref
    assert context.base_sha == pull_request.base_sha
    assert context.head_sha == pull_request.head_sha

    assert context.changed_files == [
        first_file,
        second_file,
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

    context = result[0].review_context

    assert context is not None
    assert context.changed_files == [
        supported_file,
        deleted_file,
        unsupported_file,
    ]


@pytest.mark.anyio
async def test_publish_pull_request_review_maps_findings_to_inline_comments(
    adapter: GitHubAdapter,
    github_client: AsyncMock,
    pull_request: GitHubPullRequest,
) -> None:
    changed_file = GitHubChangedFile(
        path="apps/example.py",
        status="modified",
        additions=2,
        deletions=1,
        changes=3,
        patch="""@@ -1,3 +1,4 @@
 def example():
-    return 41
+    value = 42
+    return value
 """,
    )

    finding = Finding(
        id="finding-1",
        category="correctness",
        severity="HIGH",
        description="The returned value is incorrect.",
        location=FindingLocation(line=3),
    )

    workflow_run_id = uuid4()

    github_client.create_pull_request_review.return_value = 123

    result = await adapter.publish_pull_request_review(
        pull_request=pull_request,
        changed_files=[changed_file],
        workflow_findings=[
            GitHubWorkflowFindings(
                path=changed_file.path,
                workflow_run_id=workflow_run_id,
                findings=(finding,),
            )
        ],
    )

    assert result == 123

    github_client.create_pull_request_review.assert_awaited_once()

    call_kwargs = github_client.create_pull_request_review.await_args.kwargs

    assert call_kwargs["pull_request"] is pull_request
    assert call_kwargs["commit_id"] == pull_request.head_sha
    assert call_kwargs["body"] == (
        "AI review for pull request #42.\n"
        "1 finding(s) were mapped to inline review comments."
    )

    assert len(call_kwargs["comments"]) == 1

    comment = call_kwargs["comments"][0]

    assert comment.path == "apps/example.py"
    assert comment.line == 3
    assert comment.side == "RIGHT"
    assert comment.start_line is None
    assert comment.start_side is None
    assert "finding-1" in comment.body
    assert "HIGH" in comment.body
    assert "correctness" in comment.body
    assert str(workflow_run_id) in comment.body


@pytest.mark.anyio
async def test_publish_pull_request_review_maps_multiline_finding(
    adapter: GitHubAdapter,
    github_client: AsyncMock,
    pull_request: GitHubPullRequest,
) -> None:
    changed_file = GitHubChangedFile(
        path="apps/example.py",
        status="modified",
        additions=4,
        deletions=1,
        changes=5,
        patch="""@@ -1,3 +1,6 @@
 def example():
+    first = 1
+    second = 2
+    return first + second
 """,
    )

    finding = Finding(
        id="finding-1",
        category="maintainability",
        severity="MEDIUM",
        description="These lines should be simplified.",
        location=FindingLocation(
            start_line=2,
            line=4,
        ),
    )

    github_client.create_pull_request_review.return_value = 123

    result = await adapter.publish_pull_request_review(
        pull_request=pull_request,
        changed_files=[changed_file],
        workflow_findings=[
            GitHubWorkflowFindings(
                path=changed_file.path,
                workflow_run_id=uuid4(),
                findings=(finding,),
            )
        ],
    )

    assert result == 123

    comment = github_client.create_pull_request_review.await_args.kwargs["comments"][0]

    assert comment.line == 4
    assert comment.side == "RIGHT"
    assert comment.start_line == 2
    assert comment.start_side == "RIGHT"


@pytest.mark.anyio
async def test_publish_pull_request_review_ignores_resolved_findings(
    adapter: GitHubAdapter,
    github_client: AsyncMock,
    pull_request: GitHubPullRequest,
) -> None:
    finding = Finding(
        id="finding-1",
        category="correctness",
        severity="HIGH",
        description="Already fixed.",
        status="resolved",
        location=FindingLocation(line=2),
    )

    result = await adapter.publish_pull_request_review(
        pull_request=pull_request,
        changed_files=[],
        workflow_findings=[
            GitHubWorkflowFindings(
                path="apps/example.py",
                workflow_run_id=uuid4(),
                findings=(finding,),
            )
        ],
    )

    assert result is None
    github_client.create_pull_request_review.assert_not_awaited()


@pytest.mark.anyio
async def test_publish_pull_request_review_preserves_unmapped_findings(
    adapter: GitHubAdapter,
    github_client: AsyncMock,
    pull_request: GitHubPullRequest,
) -> None:
    changed_file = GitHubChangedFile(
        path="apps/example.py",
        status="modified",
        additions=1,
        deletions=0,
        changes=1,
        patch="@@ -1 +1 @@\n-old\n+new\n",
    )

    finding = Finding(
        id="finding-1",
        category="security",
        severity="CRITICAL",
        description="Sensitive data is exposed.",
        location=FindingLocation(line=50),
    )

    workflow_run_id = uuid4()

    github_client.create_pull_request_review.return_value = 123

    result = await adapter.publish_pull_request_review(
        pull_request=pull_request,
        changed_files=[changed_file],
        workflow_findings=[
            GitHubWorkflowFindings(
                path=changed_file.path,
                workflow_run_id=workflow_run_id,
                findings=(finding,),
            )
        ],
    )

    assert result == 123

    call_kwargs = github_client.create_pull_request_review.await_args.kwargs

    assert call_kwargs["comments"] == []

    assert "Findings without a safe inline location" in call_kwargs["body"]
    assert "finding-1" in call_kwargs["body"]
    assert "CRITICAL" in call_kwargs["body"]
    assert "security" in call_kwargs["body"]
    assert "Sensitive data is exposed." in call_kwargs["body"]
    assert str(workflow_run_id) in call_kwargs["body"]


@pytest.mark.anyio
async def test_publish_pull_request_review_preserves_findings_without_patch(
    adapter: GitHubAdapter,
    github_client: AsyncMock,
    pull_request: GitHubPullRequest,
) -> None:
    changed_file = GitHubChangedFile(
        path="apps/example.py",
        status="modified",
        additions=1,
        deletions=0,
        changes=1,
        patch=None,
    )

    finding = Finding(
        id="finding-1",
        category="correctness",
        severity="HIGH",
        description="The implementation is incorrect.",
        location=FindingLocation(line=2),
    )

    github_client.create_pull_request_review.return_value = 123

    result = await adapter.publish_pull_request_review(
        pull_request=pull_request,
        changed_files=[changed_file],
        workflow_findings=[
            GitHubWorkflowFindings(
                path=changed_file.path,
                workflow_run_id=uuid4(),
                findings=(finding,),
            )
        ],
    )

    assert result == 123

    call_kwargs = github_client.create_pull_request_review.await_args.kwargs

    assert call_kwargs["comments"] == []
    assert "finding-1" in call_kwargs["body"]


@pytest.mark.anyio
async def test_publish_pull_request_review_returns_none_without_unresolved_findings(
    adapter: GitHubAdapter,
    github_client: AsyncMock,
    pull_request: GitHubPullRequest,
) -> None:
    result = await adapter.publish_pull_request_review(
        pull_request=pull_request,
        changed_files=[],
        workflow_findings=[],
    )

    assert result is None
    github_client.create_pull_request_review.assert_not_awaited()


@pytest.mark.anyio
async def test_publish_pull_request_review_uses_workflow_file_path(
    adapter: GitHubAdapter,
    github_client: AsyncMock,
    pull_request: GitHubPullRequest,
) -> None:
    changed_file = GitHubChangedFile(
        path="apps/example.py",
        status="modified",
        additions=1,
        deletions=0,
        changes=1,
        patch="@@ -1 +1 @@\n-old\n+new\n",
    )

    finding = Finding(
        id="finding-1",
        category="correctness",
        severity="HIGH",
        description="Incorrect implementation.",
        location=FindingLocation(line=1),
    )

    github_client.create_pull_request_review.return_value = 123

    await adapter.publish_pull_request_review(
        pull_request=pull_request,
        changed_files=[changed_file],
        workflow_findings=[
            GitHubWorkflowFindings(
                path="apps/example.py",
                workflow_run_id=uuid4(),
                findings=(finding,),
            )
        ],
    )

    comment = github_client.create_pull_request_review.await_args.kwargs["comments"][0]

    assert comment.path == "apps/example.py"
