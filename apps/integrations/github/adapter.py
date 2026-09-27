"""Application-facing GitHub integration adapter."""

from __future__ import annotations

from pathlib import PurePosixPath

from apps.core.constants import ALLOWED_READ_EXTENSIONS
from apps.integrations.github.client import GitHubRESTClient
from apps.integrations.github.models import (
    GitHubChangedFile,
    GitHubFileContent,
    GitHubPullRequest,
)
from apps.schemas.requests import ReviewRequest
from apps.schemas.review_context import PRContext


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

        review_context = self._build_pr_context(
            pull_request=pull_request,
            changed_files=changed_files,
        )

        contents_by_path = {
            file_content.path: file_content for file_content in file_contents
        }

        return [
            review_request
            for supported_file in supported_files
            if (
                review_request := self._build_review_request(
                    pull_request=pull_request,
                    changed_file=supported_file,
                    file_content=contents_by_path.get(supported_file.path),
                    review_context=review_context,
                )
            )
            is not None
        ]

    @staticmethod
    def _build_pr_context(
        *,
        pull_request: GitHubPullRequest,
        changed_files: list[GitHubChangedFile],
    ) -> PRContext:
        """Build PR-level review context from GitHub pull-request data."""
        return PRContext(
            pull_request_number=pull_request.number,
            title=pull_request.title,
            body=pull_request.body,
            base_ref=pull_request.base_ref,
            head_ref=pull_request.head_ref,
            base_sha=pull_request.base_sha,
            head_sha=pull_request.head_sha,
            changed_files=changed_files,
        )

    @staticmethod
    def _build_review_request(
        *,
        pull_request: GitHubPullRequest,
        changed_file: GitHubChangedFile,
        file_content: GitHubFileContent | None,
        review_context: PRContext,
    ) -> ReviewRequest | None:
        """Map one supported GitHub changed file to a review request."""

        if file_content is None:
            return None

        instruction = (
            f"Review and refactor the changes introduced by pull request "
            f"#{pull_request.number} ({pull_request.title}) in "
            f"{changed_file.path}. "
            "Consider the pull request metadata and the complete changed-file "
            "context provided in review_context when assessing this file. "
            "Preserve intended behavior and address any correctness, security, "
            "maintainability, or testing issues identified during the workflow."
        )

        return ReviewRequest(
            task_type="review_refactor",
            instruction=instruction,
            code=file_content.content,
            review_context=review_context,
        )
