"""Review context schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field

from apps.integrations.github.models import GitHubChangedFile


class PRContext(BaseModel):
    """Pull-request-level context shared by per-file review requests."""

    pull_request_number: int
    title: str
    body: str | None = None

    base_ref: str
    head_ref: str
    base_sha: str
    head_sha: str

    changed_files: list[GitHubChangedFile] = Field(default_factory=list)

    @property
    def changed_file_diffs(self) -> dict[str, str | None]:
        """Return changed-file diffs keyed by current file path."""

        return {
            changed_file.path: changed_file.patch for changed_file in self.changed_files
        }
