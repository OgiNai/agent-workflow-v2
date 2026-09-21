"""GitHub API client boundary.

The concrete REST implementation is introduced in Milestone 6.3.
Authentication and credential management are introduced in Milestone 6.2.
"""

from __future__ import annotations

from typing import Protocol

from apps.integrations.github.models import (
    GitHubChangedFile,
    GitHubFileContent,
    GitHubPullRequest,
    GitHubRepository,
)


class GitHubClient(Protocol):
    """Application-facing contract for GitHub API operations."""

    async def get_repository(
        self,
        *,
        owner: str,
        repository: str,
    ) -> GitHubRepository:
        """Retrieve repository metadata."""

    async def get_pull_request(
        self,
        *,
        owner: str,
        repository: str,
        pull_request_number: int,
    ) -> GitHubPullRequest:
        """Retrieve pull request metadata."""

    async def list_pull_request_files(
        self,
        pull_request: GitHubPullRequest,
    ) -> list[GitHubChangedFile]:
        """Retrieve files changed by a pull request."""

    async def get_file_content(
        self,
        *,
        repository: GitHubRepository,
        path: str,
        ref: str,
    ) -> GitHubFileContent:
        """Retrieve file content at a specific repository ref."""
