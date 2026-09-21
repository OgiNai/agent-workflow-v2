"""Mapping between GitHub integration models and application models."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import PurePosixPath

from apps.core.constants import ALLOWED_READ_EXTENSIONS
from apps.integrations.github.models import (
    GitHubChangedFile,
    GitHubFileContent,
    GitHubPullRequest,
)
from apps.schemas.requests import ReviewRequest


def build_review_request(
    *,
    pull_request: GitHubPullRequest,
    changed_file: GitHubChangedFile,
    file_content: GitHubFileContent | None,
) -> ReviewRequest | None:
    """Map one GitHub changed file to an application review request."""

    if not PurePosixPath(changed_file.path).suffix.lower() in ALLOWED_READ_EXTENSIONS:
        return None

    if file_content is None:
        return None

    instruction = (
        f"Review and refactor the changes introduced by pull request "
        f"#{pull_request.number} ({pull_request.title}) in "
        f"{changed_file.path}. "
        "Preserve intended behavior and address any correctness, security, "
        "maintainability, or testing issues identified during the workflow."
    )

    return ReviewRequest(
        task_type="review_refactor",
        instruction=instruction,
        code=file_content.content,
    )


def build_review_requests(
    *,
    pull_request: GitHubPullRequest,
    changed_files: Iterable[GitHubChangedFile],
    file_contents: Iterable[GitHubFileContent],
) -> list[ReviewRequest]:
    """Map supported GitHub changed files to independent review requests."""

    contents_by_path = {
        file_content.path: file_content for file_content in file_contents
    }

    requests: list[ReviewRequest] = []

    for changed_file in changed_files:
        request = build_review_request(
            pull_request=pull_request,
            changed_file=changed_file,
            file_content=contents_by_path.get(changed_file.path),
        )

        if request is not None:
            requests.append(request)

    return requests
