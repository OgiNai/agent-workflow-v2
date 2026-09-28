"""GitHub-specific integration models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias
from uuid import UUID

from apps.schemas.agent_outputs import Finding

ReviewCommentSide: TypeAlias = Literal["LEFT", "RIGHT"]

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
    ref: str  # the hash signature of the entire PR's branch
    sha: str  # the hash signature of the current state of the file itself


@dataclass(frozen=True)
class GitHubWorkflowFindings:
    """Findings produced by one file-level workflow."""

    path: str
    workflow_run_id: UUID
    findings: tuple[Finding, ...]


@dataclass(frozen=True)
class GitHubReviewComment:
    """A line-based comment included in a GitHub pull-request review."""

    path: str
    body: str
    line: int
    side: ReviewCommentSide = "RIGHT"
    start_line: int | None = None
    start_side: ReviewCommentSide | None = None


@dataclass(frozen=True)
class GitHubReviewDraft:
    """Normalized review payload prepared by the adapter."""

    body: str
    comments: tuple[GitHubReviewComment, ...]
