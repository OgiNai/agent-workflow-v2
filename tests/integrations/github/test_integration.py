"""Integration tests for the GitHub adapter and REST client."""

from __future__ import annotations

import base64
import json
from uuid import uuid4

import httpx2
import pytest

from apps.integrations.github.adapter import GitHubAdapter
from apps.integrations.github.client import GitHubRESTClient
from apps.integrations.github.errors import (
    GitHubAPIError,
    GitHubAuthenticationError,
)
from apps.integrations.github.models import (
    GitHubChangedFile,
    GitHubPullRequest,
    GitHubRepository,
    GitHubWorkflowFindings,
)
from apps.schemas.agent_outputs import Finding, FindingLocation

REPOSITORY = GitHubRepository(
    owner="example-owner",
    name="example-repo",
    default_branch="main",
)

PULL_REQUEST = GitHubPullRequest(
    number=42,
    title="Improve example implementation",
    body="Refactor the example implementation.",
    base_ref="main",
    head_ref="feature/example",
    base_sha="base-sha-123",
    head_sha="head-sha-456",
    repository=REPOSITORY,
)


def make_http_client(
    handler,
) -> httpx2.AsyncClient:
    return httpx2.AsyncClient(
        transport=httpx2.MockTransport(handler),
        base_url="https://api.github.test",
    )


def make_adapter(
    http_client: httpx2.AsyncClient,
) -> GitHubAdapter:
    github_client = GitHubRESTClient(client=http_client)
    return GitHubAdapter(github_client)


@pytest.mark.anyio
async def test_build_review_requests_integrates_adapter_with_github_client() -> None:
    first_file = GitHubChangedFile(
        path="apps/first.py",
        status="modified",
        additions=2,
        deletions=1,
        changes=3,
        patch="@@ -1 +1,2 @@",
    )
    second_file = GitHubChangedFile(
        path="apps/second.py",
        status="added",
        additions=3,
        deletions=0,
        changes=3,
        patch="@@ -0,0 +1,3 @@",
    )

    first_content = "def first():\n    return 1\n"
    second_content = "def second():\n    return 2\n"

    first_encoded = base64.b64encode(first_content.encode()).decode()
    second_encoded = base64.b64encode(second_content.encode()).decode()

    async def handler(request: httpx2.Request) -> httpx2.Response:
        if request.method == "GET" and request.url.path == (
            "/repos/example-owner/example-repo/pulls/42/files"
        ):
            return httpx2.Response(
                200,
                json=[
                    {
                        "filename": first_file.path,
                        "status": first_file.status,
                        "additions": first_file.additions,
                        "deletions": first_file.deletions,
                        "changes": first_file.changes,
                        "patch": first_file.patch,
                    },
                    {
                        "filename": second_file.path,
                        "status": second_file.status,
                        "additions": second_file.additions,
                        "deletions": second_file.deletions,
                        "changes": second_file.changes,
                        "patch": second_file.patch,
                    },
                ],
                request=request,
            )

        if request.method == "GET" and request.url.path == (
            "/repos/example-owner/example-repo/contents/apps/first.py"
        ):
            assert request.url.params["ref"] == PULL_REQUEST.head_sha

            return httpx2.Response(
                200,
                json={
                    "path": first_file.path,
                    "content": first_encoded,
                    "encoding": "base64",
                    "sha": "first-sha",
                    "type": "file",
                },
                request=request,
            )

        if request.method == "GET" and request.url.path == (
            "/repos/example-owner/example-repo/contents/apps/second.py"
        ):
            assert request.url.params["ref"] == PULL_REQUEST.head_sha

            return httpx2.Response(
                200,
                json={
                    "path": second_file.path,
                    "content": second_encoded,
                    "encoding": "base64",
                    "sha": "second-sha",
                    "type": "file",
                },
                request=request,
            )

        return httpx2.Response(404, json={"message": "Not found"}, request=request)

    http_client = make_http_client(handler)

    try:
        adapter = make_adapter(http_client)

        result = await adapter.build_review_requests(PULL_REQUEST)

        assert len(result) == 2

        assert [request.code for request in result] == [
            first_content,
            second_content,
        ]

        assert all(request.task_type == "review_refactor" for request in result)

        assert result[0].review_context is result[1].review_context

        context = result[0].review_context

        assert context is not None
        assert context.pull_request_number == PULL_REQUEST.number
        assert context.title == PULL_REQUEST.title
        assert context.body == PULL_REQUEST.body
        assert context.base_ref == PULL_REQUEST.base_ref
        assert context.head_ref == PULL_REQUEST.head_ref
        assert context.base_sha == PULL_REQUEST.base_sha
        assert context.head_sha == PULL_REQUEST.head_sha
        assert context.changed_files == [
            first_file,
            second_file,
        ]
    finally:
        await http_client.aclose()


@pytest.mark.anyio
async def test_build_review_requests_propagates_authentication_failure() -> None:
    async def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            401,
            json={"message": "Bad credentials"},
            request=request,
        )

    http_client = make_http_client(handler)

    try:
        adapter = make_adapter(http_client)

        with pytest.raises(GitHubAuthenticationError):
            await adapter.build_review_requests(PULL_REQUEST)
    finally:
        await http_client.aclose()


@pytest.mark.anyio
async def test_build_review_requests_propagates_file_retrieval_failure() -> None:
    changed_file = GitHubChangedFile(
        path="apps/example.py",
        status="modified",
        additions=2,
        deletions=1,
        changes=3,
        patch="@@ -1 +1,2 @@",
    )

    async def handler(request: httpx2.Request) -> httpx2.Response:
        if request.url.path == ("/repos/example-owner/example-repo/pulls/42/files"):
            return httpx2.Response(
                200,
                json=[
                    {
                        "filename": changed_file.path,
                        "status": changed_file.status,
                        "additions": changed_file.additions,
                        "deletions": changed_file.deletions,
                        "changes": changed_file.changes,
                        "patch": changed_file.patch,
                    }
                ],
                request=request,
            )

        if request.url.path == (
            "/repos/example-owner/example-repo/contents/apps/example.py"
        ):
            return httpx2.Response(
                404,
                json={"message": "File not found"},
                request=request,
            )

        return httpx2.Response(404, json={"message": "Not found"}, request=request)

    http_client = make_http_client(handler)

    try:
        adapter = make_adapter(http_client)

        with pytest.raises(GitHubAPIError):
            await adapter.build_review_requests(PULL_REQUEST)
    finally:
        await http_client.aclose()


@pytest.mark.anyio
async def test_build_review_requests_propagates_malformed_file_response() -> None:
    changed_file = GitHubChangedFile(
        path="apps/example.py",
        status="modified",
        additions=2,
        deletions=1,
        changes=3,
        patch="@@ -1 +1,2 @@",
    )

    async def handler(request: httpx2.Request) -> httpx2.Response:
        if request.url.path == ("/repos/example-owner/example-repo/pulls/42/files"):
            return httpx2.Response(
                200,
                json=[
                    {
                        "filename": changed_file.path,
                        "status": changed_file.status,
                        "additions": changed_file.additions,
                        "deletions": changed_file.deletions,
                        "changes": changed_file.changes,
                        "patch": changed_file.patch,
                    }
                ],
                request=request,
            )

        if request.url.path == (
            "/repos/example-owner/example-repo/contents/apps/example.py"
        ):
            return httpx2.Response(
                200,
                json={
                    "path": changed_file.path,
                    "content": "not-base64",
                    "encoding": "base64",
                    "sha": "file-sha",
                    "type": "file",
                },
                request=request,
            )

        return httpx2.Response(404, json={"message": "Not found"}, request=request)

    http_client = make_http_client(handler)

    try:
        adapter = make_adapter(http_client)

        with pytest.raises(GitHubAPIError):
            await adapter.build_review_requests(PULL_REQUEST)
    finally:
        await http_client.aclose()


@pytest.mark.anyio
async def test_publish_pull_request_review_integrates_adapter_with_github_client() -> (
    None
):
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

    workflow_run_id = uuid4()

    finding = Finding(
        id="finding-1",
        category="correctness",
        severity="HIGH",
        description="The returned value is incorrect.",
        location=FindingLocation(line=3),
    )

    async def handler(request: httpx2.Request) -> httpx2.Response:
        assert request.method == "POST"
        assert request.url.path == (
            "/repos/example-owner/example-repo/pulls/42/reviews"
        )

        payload = json.loads(request.content)

        assert payload == {
            "commit_id": PULL_REQUEST.head_sha,
            "body": (
                "AI review for pull request #42.\n"
                "1 finding(s) were mapped to inline review comments."
            ),
            "event": "COMMENT",
            "comments": [
                {
                    "path": changed_file.path,
                    "body": (
                        "**[HIGH] correctness** — `finding-1`\n\n"
                        "The returned value is incorrect.\n\n"
                        f"Workflow run: `{workflow_run_id}`"
                    ),
                    "line": 3,
                    "side": "RIGHT",
                }
            ],
        }

        return httpx2.Response(
            200,
            json={"id": 12345},
            request=request,
        )

    http_client = make_http_client(handler)

    try:
        adapter = make_adapter(http_client)

        review_id = await adapter.publish_pull_request_review(
            pull_request=PULL_REQUEST,
            changed_files=[changed_file],
            workflow_findings=[
                GitHubWorkflowFindings(
                    path=changed_file.path,
                    workflow_run_id=workflow_run_id,
                    findings=(finding,),
                )
            ],
        )

        assert review_id == 12345
    finally:
        await http_client.aclose()
