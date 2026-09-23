"""GitHub REST API client."""

from __future__ import annotations

import base64
from typing import Any, Self, get_args

import httpx2

from apps.core.constants import (
    DEFAULT_TIMEOUT_SECONDS,
    GITHUB_ACCEPT_HEADER,
    GITHUB_API_BASE_URL,
    GITHUB_API_VERSION,
    MAX_FILE_SIZE_BYTES,
    PER_PAGE,
)
from apps.core.settings import get_auth_settings
from apps.integrations.github.errors import (
    GitHubAPIError,
    GitHubAuthenticationError,
    GitHubAuthorizationError,
)
from apps.integrations.github.models import (
    ChangedFileStatus,
    GitHubChangedFile,
    GitHubFileContent,
    GitHubPullRequest,
    GitHubRepository,
)


class GitHubRESTClient:
    """Concrete GitHub REST API client used by the integration adapter."""

    def __init__(
        self,
        client: httpx2.AsyncClient | None = None,
    ) -> None:
        self._client = client

        # if GitHubRESTClient is constructed with provided existing client then
        # GitHubRESTClient does not own it and therefore does not close it
        # if no client is supplied GitHubRESTClient creates its own httpx2.AsyncClient,
        # owns it, and closes it when the REST client is closed
        self._need_to_close_client = client is None

    async def __aenter__(self) -> Self:
        if self._client is None:
            self._client = httpx2.AsyncClient(
                base_url=GITHUB_API_BASE_URL,
                timeout=DEFAULT_TIMEOUT_SECONDS,
            )
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def close(self) -> None:
        if self._client is not None and self._need_to_close_client:
            await self._client.aclose()
            self._client = None

    def _get_client(self) -> httpx2.AsyncClient:
        if self._client is None:
            self._client = httpx2.AsyncClient(
                base_url=GITHUB_API_BASE_URL,
                timeout=DEFAULT_TIMEOUT_SECONDS,
            )
        return self._client

    def _build_headers(self) -> dict[str, str]:

        return {
            "Accept": GITHUB_ACCEPT_HEADER,
            "Authorization": (
                f"Bearer {get_auth_settings().github_token.get_secret_value()}"
            ),
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
        }

    async def _get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        client = self._get_client()

        try:
            response = await client.get(
                path,
                headers=self._build_headers(),
                params=params,
            )
        except httpx2.RequestError as exc:
            raise GitHubAPIError("GitHub request failed.") from exc

        if response.status_code == 401:
            raise GitHubAuthenticationError("GitHub authentication failed.")

        if response.status_code == 403:
            raise GitHubAuthorizationError("GitHub authorization failed.")

        if response.status_code >= 400:
            raise GitHubAPIError(
                f"GitHub API request failed with status {response.status_code}."
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise GitHubAPIError("GitHub returned an invalid JSON response.") from exc

        if not isinstance(payload, (dict, list)):
            raise GitHubAPIError("GitHub returned an unexpected response format.")

        return payload

    @staticmethod
    def _require_string(
        payload: dict[str, Any],
        field: str,
    ) -> str:
        value = payload.get(field)

        if not isinstance(value, str) or not value.strip():
            raise GitHubAPIError(f"GitHub response is missing a valid '{field}' field.")

        return value

    @staticmethod
    def _require_int(
        payload: dict[str, Any],
        field: str,
    ) -> int:
        value = payload.get(field)

        if not isinstance(value, int):
            raise GitHubAPIError(f"GitHub response is missing a valid '{field}' field.")

        return value

    async def get_repository(
        self,
        *,
        owner: str,
        repository_name: str,
    ) -> GitHubRepository:
        payload = await self._get(
            f"/repos/{owner}/{repository_name}",
        )

        if not isinstance(payload, dict):
            raise GitHubAPIError("GitHub repository response has an unexpected format.")

        response_owner = payload.get("owner")
        if not isinstance(response_owner, dict):
            raise GitHubAPIError(
                "GitHub repository response is missing owner metadata."
            )

        owner_login = self._require_string(response_owner, "login")
        name = self._require_string(payload, "name")
        default_branch = self._require_string(payload, "default_branch")

        return GitHubRepository(
            owner=owner_login,
            name=name,
            default_branch=default_branch,
        )

    async def get_pull_request(
        self,
        *,
        repository: GitHubRepository,
        pull_request_number: int,
    ) -> GitHubPullRequest:
        """Retrieve pull request metadata from GitHub."""

        payload = await self._get(
            f"/repos/{repository.owner}/{repository.name}/pulls/{pull_request_number}",
        )

        if not isinstance(payload, dict):
            raise GitHubAPIError(
                "GitHub pull request response has an unexpected format."
            )

        base = payload.get("base")
        head = payload.get("head")

        if not isinstance(base, dict) or not isinstance(head, dict):
            raise GitHubAPIError(
                "GitHub pull request response is missing ref metadata."
            )

        base_ref = self._require_string(base, "ref")
        head_ref = self._require_string(head, "ref")

        base_sha = self._require_string(base, "sha")
        head_sha = self._require_string(head, "sha")

        body = payload.get("body")
        if body is not None and not isinstance(body, str):
            raise GitHubAPIError("GitHub pull request body has an unexpected format.")

        return GitHubPullRequest(
            number=self._require_int(payload, "number"),
            title=self._require_string(payload, "title"),
            body=body,
            base_ref=base_ref,
            head_ref=head_ref,
            base_sha=base_sha,
            head_sha=head_sha,
            repository=repository,
        )

    async def list_pull_request_files(
        self,
        pull_request: GitHubPullRequest,
    ) -> list[GitHubChangedFile]:
        """Paginated retrieval of changed files"""

        changed_files: list[GitHubChangedFile] = []
        page = 1

        while True:
            payload = await self._get(
                f"/repos/{pull_request.repository.owner}/"
                f"{pull_request.repository.name}/pulls/"
                f"{pull_request.number}/files",
                params={
                    "per_page": PER_PAGE,
                    "page": page,
                },
            )

            if not isinstance(payload, list):
                raise GitHubAPIError(
                    "GitHub changed-files response has an unexpected format."
                )

            for item in payload:
                if not isinstance(item, dict):
                    raise GitHubAPIError(
                        "GitHub changed-file entry has an unexpected format."
                    )

                status = item.get("status")

                if status not in get_args(ChangedFileStatus):
                    raise GitHubAPIError("GitHub returned an unsupported file status.")

                previous_path = item.get("previous_filename")
                if previous_path is not None and not isinstance(
                    previous_path,
                    str,
                ):
                    raise GitHubAPIError(
                        "GitHub previous filename has an unexpected format."
                    )

                patch = item.get("patch")
                if patch is not None and not isinstance(patch, str):
                    raise GitHubAPIError("GitHub patch has an unexpected format.")

                changed_files.append(
                    GitHubChangedFile(
                        path=self._require_string(item, "filename"),
                        status=status,
                        additions=self._require_int(item, "additions"),
                        deletions=self._require_int(item, "deletions"),
                        changes=self._require_int(item, "changes"),
                        previous_path=previous_path,
                        patch=patch,
                    )
                )

            if len(payload) < PER_PAGE:
                break

            page += 1

        return changed_files

    async def get_file_content(
        self,
        *,
        repository: GitHubRepository,
        path: str,
        ref: str,
    ) -> GitHubFileContent:
        payload = await self._get(
            f"/repos/{repository.owner}/{repository.name}/contents/{path}",
            params={"ref": ref},
        )

        if not isinstance(payload, dict):
            raise GitHubAPIError(
                "GitHub file-content response has an unexpected format."
            )

        if payload.get("type") != "file":
            raise GitHubAPIError("GitHub content response does not describe a file.")

        encoding = payload.get("encoding")
        encoded_content = payload.get("content")

        if encoding != "base64" or not isinstance(encoded_content, str):
            raise GitHubAPIError("GitHub file content is not returned as base64.")

        try:
            content = base64.b64decode(
                encoded_content,
                validate=True,
            ).decode("utf-8")
        except (ValueError, UnicodeDecodeError) as exc:
            raise GitHubAPIError("GitHub file content could not be decoded.") from exc

        if len(content.encode("utf-8")) > MAX_FILE_SIZE_BYTES:
            raise GitHubAPIError("GitHub file exceeds the configured size limit.")

        return GitHubFileContent(
            path=self._require_string(payload, "path"),
            content=content,
            ref=ref,
            sha=self._require_string(payload, "sha"),
        )
