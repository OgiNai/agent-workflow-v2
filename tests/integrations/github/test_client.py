"""Tests for the GitHub REST client."""

from __future__ import annotations

import base64

import httpx2
import pytest

from apps.core.settings import get_auth_settings
from apps.integrations.github.client import GitHubRESTClient
from apps.integrations.github.errors import (
    GitHubAPIError,
    GitHubAuthenticationError,
    GitHubAuthorizationError,
)
from apps.integrations.github.models import GitHubPullRequest, GitHubRepository

TOKEN = get_auth_settings().github_token.get_secret_value()

REPOSITORY_PAYLOAD = {
    "name": "example-repo",
    "owner": {"login": "example-owner"},
    "default_branch": "main",
}

PULL_REQUEST_PAYLOAD = {
    "number": 42,
    "title": "Improve example implementation",
    "body": "Refactor the example implementation.",
    "base": {
        "ref": "main",
        "sha": "base-sha-123",
    },
    "head": {
        "ref": "feature/example",
        "sha": "head-sha-456",
    },
}

PULL_REQUEST_FILES_PAYLOAD = [
    {
        "filename": "apps/example.py",
        "status": "modified",
        "additions": 10,
        "deletions": 3,
        "changes": 13,
        "patch": "@@ -1,3 +1,10 @@",
    },
    {
        "filename": "tests/test_example.py",
        "status": "added",
        "additions": 20,
        "deletions": 0,
        "changes": 20,
        "patch": "@@ -0,0 +1,20 @@",
    },
]

FILE_CONTENT = "def example():\n    return 42\n"
FILE_SHA = "file-sha-789"


def make_http_client(
    handler,
) -> httpx2.AsyncClient:
    return httpx2.AsyncClient(
        transport=httpx2.MockTransport(handler),
        base_url="https://api.github.test",
    )


def make_rest_client(
    http_client: httpx2.AsyncClient,
) -> GitHubRESTClient:
    return GitHubRESTClient(
        client=http_client,
    )


async def _make_pull_request(
    repository: GitHubRepository,
):
    return GitHubPullRequest(
        number=42,
        title="Improve example implementation",
        body="Refactor the example implementation.",
        base_ref="main",
        head_ref="feature/example",
        base_sha="base-sha-123",
        head_sha="head-sha-456",
        repository=repository,
    )


@pytest.mark.anyio
async def test_get_repository_maps_response() -> None:
    async def handler(request: httpx2.Request) -> httpx2.Response:
        assert request.method == "GET"
        assert request.url.path == "/repos/example-owner/example-repo"
        return httpx2.Response(
            200,
            json=REPOSITORY_PAYLOAD,
            request=request,
        )

    http_client = make_http_client(handler)

    try:
        github_client = make_rest_client(http_client)

        repository = await github_client.get_repository(
            owner="example-owner",
            repository_name="example-repo",
        )

        assert repository.owner == "example-owner"
        assert repository.name == "example-repo"
        assert repository.default_branch == "main"
        assert repository.full_name == "example-owner/example-repo"
    finally:
        await http_client.aclose()


@pytest.mark.anyio
async def test_get_pull_request_maps_response_and_reuses_repository() -> None:
    repository = GitHubRepository(
        owner="example-owner",
        name="example-repo",
        default_branch="main",
    )

    async def handler(request: httpx2.Request) -> httpx2.Response:
        assert request.method == "GET"
        assert request.url.path == "/repos/example-owner/example-repo/pulls/42"
        return httpx2.Response(
            200,
            json=PULL_REQUEST_PAYLOAD,
            request=request,
        )

    http_client = make_http_client(handler)

    try:
        github_client = make_rest_client(http_client)

        pull_request = await github_client.get_pull_request(
            repository=repository,
            pull_request_number=42,
        )

        assert pull_request.number == 42
        assert pull_request.title == "Improve example implementation"
        assert pull_request.body == "Refactor the example implementation."
        assert pull_request.base_ref == "main"
        assert pull_request.head_ref == "feature/example"
        assert pull_request.base_sha == "base-sha-123"
        assert pull_request.head_sha == "head-sha-456"
        assert pull_request.repository is repository
    finally:
        await http_client.aclose()


@pytest.mark.anyio
async def test_get_pull_request_allows_null_body() -> None:
    repository = GitHubRepository(
        owner="example-owner",
        name="example-repo",
        default_branch="main",
    )

    payload = {
        **PULL_REQUEST_PAYLOAD,
        "body": None,
    }

    async def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            200,
            json=payload,
            request=request,
        )

    http_client = make_http_client(handler)

    try:
        github_client = make_rest_client(http_client)

        pull_request = await github_client.get_pull_request(
            repository=repository,
            pull_request_number=42,
        )

        assert pull_request.body is None
    finally:
        await http_client.aclose()


@pytest.mark.anyio
async def test_list_pull_request_files_maps_response() -> None:
    repository = GitHubRepository(
        owner="example-owner",
        name="example-repo",
        default_branch="main",
    )

    pull_request = await _make_pull_request(repository)

    async def handler(request: httpx2.Request) -> httpx2.Response:
        assert request.method == "GET"
        assert request.url.path == ("/repos/example-owner/example-repo/pulls/42/files")
        assert request.url.params["per_page"] == "100"

        return httpx2.Response(
            200,
            json=PULL_REQUEST_FILES_PAYLOAD,
            request=request,
        )

    http_client = make_http_client(handler)

    try:
        github_client = make_rest_client(http_client)

        files = await github_client.list_pull_request_files(pull_request)

        assert len(files) == 2

        assert files[0].path == "apps/example.py"
        assert files[0].status == "modified"
        assert files[0].additions == 10
        assert files[0].deletions == 3
        assert files[0].changes == 13
        assert files[0].patch == "@@ -1,3 +1,10 @@"

        assert files[1].path == "tests/test_example.py"
        assert files[1].status == "added"
    finally:
        await http_client.aclose()


@pytest.mark.anyio
async def test_list_pull_request_files_follows_pagination() -> None:
    from apps.core.constants import PER_PAGE

    repository = GitHubRepository(
        owner="example-owner",
        name="example-repo",
        default_branch="main",
    )

    pull_request = await _make_pull_request(repository)
    requested_pages: list[str] = []

    first_page = [
        {
            "filename": f"apps/example_{index}.py",
            "status": "modified",
            "additions": 1,
            "deletions": 0,
            "changes": 1,
        }
        for index in range(PER_PAGE)
    ]

    second_page = [
        {
            "filename": "tests/test_example.py",
            "status": "added",
            "additions": 2,
            "deletions": 0,
            "changes": 2,
        }
    ]

    async def handler(request: httpx2.Request) -> httpx2.Response:
        page = request.url.params["page"]
        requested_pages.append(page)

        payload = first_page if page == "1" else second_page

        return httpx2.Response(
            200,
            json=payload,
            request=request,
        )

    http_client = make_http_client(handler)

    try:
        github_client = make_rest_client(http_client)

        files = await github_client.list_pull_request_files(pull_request)

        assert requested_pages == ["1", "2"]
        assert len(files) == PER_PAGE + 1
        assert files[0].path == "apps/example_0.py"
        assert files[-1].path == "tests/test_example.py"
    finally:
        await http_client.aclose()


@pytest.mark.anyio
async def test_get_file_content_decodes_base64_content() -> None:
    repository = GitHubRepository(
        owner="example-owner",
        name="example-repo",
        default_branch="main",
    )

    encoded_content = base64.b64encode(FILE_CONTENT.encode()).decode()

    async def handler(request: httpx2.Request) -> httpx2.Response:
        assert request.method == "GET"
        assert request.url.path == (
            "/repos/example-owner/example-repo/contents/apps/example.py"
        )
        assert request.url.params["ref"] == "head-sha-456"

        return httpx2.Response(
            200,
            json={
                "path": "apps/example.py",
                "content": encoded_content,
                "encoding": "base64",
                "sha": FILE_SHA,
                "type": "file",
            },
            request=request,
        )

    http_client = make_http_client(handler)

    try:
        github_client = make_rest_client(http_client)

        file_content = await github_client.get_file_content(
            repository=repository,
            path="apps/example.py",
            ref="head-sha-456",
        )

        assert file_content.path == "apps/example.py"
        assert file_content.content == FILE_CONTENT
        assert file_content.ref == "head-sha-456"
        assert file_content.sha == FILE_SHA
    finally:
        await http_client.aclose()


@pytest.mark.anyio
async def test_requests_include_github_authentication_headers() -> None:
    async def handler(request: httpx2.Request) -> httpx2.Response:
        assert request.headers["Authorization"] == f"Bearer {TOKEN}"
        assert request.headers["Accept"] == "application/vnd.github+json"
        assert "X-GitHub-Api-Version" in request.headers

        return httpx2.Response(
            200,
            json=REPOSITORY_PAYLOAD,
            request=request,
        )

    http_client = make_http_client(handler)

    try:
        github_client = make_rest_client(http_client)

        await github_client.get_repository(
            owner="example-owner",
            repository_name="example-repo",
        )
    finally:
        await http_client.aclose()


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("status_code", "expected_exception"),
    [
        (401, GitHubAuthenticationError),
        (403, GitHubAuthorizationError),
        (404, GitHubAPIError),
        (422, GitHubAPIError),
        (500, GitHubAPIError),
    ],
)
async def test_github_http_errors_are_mapped(
    status_code: int,
    expected_exception: type[Exception],
) -> None:
    async def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            status_code,
            json={"message": "GitHub API error"},
            request=request,
        )

    http_client = make_http_client(handler)

    try:
        github_client = make_rest_client(http_client)

        with pytest.raises(expected_exception):
            await github_client.get_repository(
                owner="example-owner",
                repository_name="example-repo",
            )
    finally:
        await http_client.aclose()


@pytest.mark.anyio
async def test_malformed_repository_response_raises_github_api_error() -> None:
    async def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            200,
            json={
                "name": "example-repo",
                "owner": {"login": "example-owner"},
                "default_branch": 123,
            },
            request=request,
        )

    http_client = make_http_client(handler)

    try:
        github_client = make_rest_client(http_client)

        with pytest.raises(GitHubAPIError):
            await github_client.get_repository(
                owner="example-owner",
                repository_name="example-repo",
            )
    finally:
        await http_client.aclose()


@pytest.mark.anyio
async def test_malformed_pull_request_response_raises_github_api_error() -> None:
    repository = GitHubRepository(
        owner="example-owner",
        name="example-repo",
        default_branch="main",
    )

    async def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            200,
            json={
                **PULL_REQUEST_PAYLOAD,
                "base": "invalid",
            },
            request=request,
        )

    http_client = make_http_client(handler)

    try:
        github_client = make_rest_client(http_client)

        with pytest.raises(GitHubAPIError):
            await github_client.get_pull_request(
                repository=repository,
                pull_request_number=42,
            )
    finally:
        await http_client.aclose()


@pytest.mark.anyio
async def test_malformed_pull_request_body_raises_github_api_error() -> None:
    repository = GitHubRepository(
        owner="example-owner",
        name="example-repo",
        default_branch="main",
    )

    async def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            200,
            json={
                **PULL_REQUEST_PAYLOAD,
                "body": 123,
            },
            request=request,
        )

    http_client = make_http_client(handler)

    try:
        github_client = make_rest_client(http_client)

        with pytest.raises(GitHubAPIError):
            await github_client.get_pull_request(
                repository=repository,
                pull_request_number=42,
            )
    finally:
        await http_client.aclose()


@pytest.mark.anyio
async def test_injected_client_is_not_closed_by_github_rest_client() -> None:
    async def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            200,
            json=REPOSITORY_PAYLOAD,
            request=request,
        )

    http_client = make_http_client(handler)
    github_client = make_rest_client(http_client)

    await github_client.close()

    assert not http_client.is_closed

    await http_client.aclose()
