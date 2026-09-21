"""GitHub-specific integration models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class GitHubRepository:
    """Repository metadata retrieved from GitHub."""

    owner: str
    name: str
    default_branch: str

    @property
    def full_name(self) -> str:
        """Return the repository's owner/name identifier."""
        return f"{self.owner}/{self.name}"


@dataclass(frozen=True)
class GitHubPullRequest:
    """Pull request metadata retrieved from GitHub."""

    number: int
    title: str
    body: str | None
    base_ref: str
    head_ref: str
    base_sha: str
    head_sha: str
    repository: GitHubRepository


@dataclass(frozen=True)
class GitHubChangedFile:
    """A file changed by a GitHub pull request."""

    path: str
    status: Literal["added", "modified", "removed", "renamed", "copied"]
    additions: int
    deletions: int
    changes: int
    previous_path: str | None = None
    patch: str | None = None


@dataclass(frozen=True)
class GitHubFileContent:
    """Source content retrieved from a GitHub repository."""

    path: str
    content: str
    ref: str
    sha: str


@dataclass(frozen=True)
class GitHubPullRequestData:
    """Complete GitHub data required to prepare a PR for review."""

    pull_request: GitHubPullRequest
    changed_files: tuple[GitHubChangedFile, ...]
    file_contents: tuple[GitHubFileContent, ...]
