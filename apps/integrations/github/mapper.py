"""Mapping between GitHub integration models and application models."""

from __future__ import annotations

from pathlib import PurePosixPath

from apps.core.constants import ALLOWED_READ_EXTENSIONS
from apps.integrations.github.models import (
    GitHubChangedFile,
    GitHubFileContent,
    GitHubPullRequest,
)
from apps.schemas.requests import ReviewRequest
from apps.schemas.review_context import PRContext


def build_pr_context(
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


def build_review_request(
    *,
    pull_request: GitHubPullRequest,
    changed_file: GitHubChangedFile,
    file_content: GitHubFileContent | None,
    review_context: PRContext,
) -> ReviewRequest | None:
    """Map one GitHub changed file to an application review request."""

    if not PurePosixPath(changed_file.path).suffix.lower() in ALLOWED_READ_EXTENSIONS:
        return None

    if changed_file.status == "deleted":
        return None

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


def build_review_requests(
    *,
    pull_request: GitHubPullRequest,
    changed_files: list[GitHubChangedFile],
    file_contents: list[GitHubFileContent],
) -> list[ReviewRequest]:
    """Map supported GitHub changed files to independent review requests."""

    contents_by_path = {
        file_content.path: file_content for file_content in file_contents
    }

    review_context = build_pr_context(
        pull_request=pull_request,
        changed_files=changed_files,
    )

    requests: list[ReviewRequest] = []

    for changed_file in changed_files:
        request = build_review_request(
            pull_request=pull_request,
            changed_file=changed_file,
            file_content=contents_by_path.get(changed_file.path),
            review_context=review_context,
        )

        if request is not None:
            requests.append(request)

    return requests
