"""Application-facing GitHub integration adapter."""

from __future__ import annotations

from pathlib import PurePosixPath

from apps.core.constants import ALLOWED_READ_EXTENSIONS
from apps.integrations.github.client import GitHubRESTClient
from apps.integrations.github.mapper import build_review_requests
from apps.integrations.github.models import GitHubPullRequest
from apps.schemas.requests import ReviewRequest


class GitHubAdapter:
    """Translate GitHub resources into application workflow inputs."""

    def __init__(self, client: GitHubRESTClient) -> None:
        self.client = client

    async def build_review_requests(
        self,
        pull_request: GitHubPullRequest,
    ) -> list[ReviewRequest]:
        """Retrieve and map supported pull request files to workflow requests."""
        repository = pull_request.repository

        changed_files = await self.client.list_pull_request_files(
            pull_request,
        )

        supported_files = [
            changed_file
            for changed_file in changed_files
            if changed_file.status != "deleted"
            and PurePosixPath(changed_file.path).suffix.lower()
            in ALLOWED_READ_EXTENSIONS
        ]

        file_contents = [
            await self.client.get_file_content(
                repository=repository,
                path=changed_file.path,
                ref=pull_request.head_sha,
            )
            for changed_file in supported_files
        ]

        return build_review_requests(
            pull_request=pull_request,
            changed_files=supported_files,
            file_contents=file_contents,
        )
