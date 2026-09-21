"""Application-facing GitHub integration adapter."""

from __future__ import annotations

from apps.integrations.github.client import GitHubClient
from apps.integrations.github.mapper import build_review_requests
from apps.integrations.github.models import GitHubPullRequestData
from apps.schemas.requests import ReviewRequest


class GitHubAdapter:
    """Translate GitHub resources into application workflow inputs."""

    def __init__(self, client: GitHubClient) -> None:
        self.client = client

    async def get_pull_request_data(
        self,
        *,
        owner: str,
        repository: str,
        pull_request_number: int,
    ) -> GitHubPullRequestData:
        """Retrieve the GitHub data required to review a pull request."""
        pull_request = await self.client.get_pull_request(
            owner=owner,
            repository=repository,
            pull_request_number=pull_request_number,
        )

        changed_files = await self.client.list_pull_request_files(
            owner=owner,
            repository=repository,
            pull_request_number=pull_request_number,
        )

        file_contents = []

        for changed_file in changed_files:
            if changed_file.status == "removed":
                continue

            file_content = await self.client.get_file_content(
                owner=owner,
                repository=repository,
                path=changed_file.path,
                ref=pull_request.head_sha,
            )
            file_contents.append(file_content)

        return GitHubPullRequestData(
            pull_request=pull_request,
            changed_files=tuple(changed_files),
            file_contents=tuple(file_contents),
        )

    def build_review_requests(
        self,
        data: GitHubPullRequestData,
    ) -> list[ReviewRequest]:
        """Convert supported changed files into workflow requests."""
        return build_review_requests(
            pull_request=data.pull_request,
            changed_files=data.changed_files,
            file_contents=data.file_contents,
        )
