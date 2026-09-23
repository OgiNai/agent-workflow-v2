"""GitHub-specific integration models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias

ChangedFileStatus: TypeAlias = Literal[
    "added",
    "modified",
    "deleted",
    "renamed",
    "copied",
]


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
    status: ChangedFileStatus
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
