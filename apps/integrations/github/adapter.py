"""Application-facing GitHub integration adapter."""

from __future__ import annotations

import re
from pathlib import PurePosixPath

from apps.core.constants import ALLOWED_READ_EXTENSIONS
from apps.integrations.github.client import GitHubRESTClient
from apps.integrations.github.models import (
    GitHubChangedFile,
    GitHubFileContent,
    GitHubPullRequest,
    GitHubReviewComment,
    GitHubReviewDraft,
    GitHubWorkflowFindings,
)
from apps.schemas.agent_outputs import Finding
from apps.schemas.requests import ReviewRequest
from apps.schemas.review_context import PRContext

_HUNK_HEADER_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(?P<new_start>\d+)(?:,(?:\d+))? @@")


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

    async def publish_pull_request_review(
        self,
        *,
        pull_request: GitHubPullRequest,
        changed_files: list[GitHubChangedFile],
        workflow_findings: list[GitHubWorkflowFindings],
    ) -> int | None:
        """Publish one COMMENT review containing all currently unresolved findings."""

        draft = self.build_review_draft(
            pull_request=pull_request,
            changed_files=changed_files,
            workflow_findings=workflow_findings,
        )

        if draft is None:
            return None

        return await self.client.create_pull_request_review(
            pull_request=pull_request,
            commit_id=pull_request.head_sha,
            body=draft.body,
            comments=list(draft.comments),
        )

    @classmethod
    def build_review_draft(
        cls,
        *,
        pull_request: GitHubPullRequest,
        changed_files: list[GitHubChangedFile],
        workflow_findings: list[GitHubWorkflowFindings],
    ) -> GitHubReviewDraft | None:
        """Map unresolved findings to inline comments or the review summary."""

        changed_files_by_path = {
            changed_file.path: changed_file for changed_file in changed_files
        }

        comments: list[GitHubReviewComment] = []
        unmapped: list[GitHubWorkflowFindings] = []
        current_findings = 0

        for workflow_group in workflow_findings:
            changed_file = changed_files_by_path.get(workflow_group.path)

            for finding in workflow_group.findings:
                if finding.status != "unresolved":
                    continue

                current_findings += 1

                comment = cls._build_review_comment(
                    finding=finding,
                    changed_file=changed_file,
                    workflow_run_id=str(workflow_group.workflow_run_id),
                    path=workflow_group.path,
                )

                if comment is None:
                    unmapped.append(
                        GitHubWorkflowFindings(
                            path=workflow_group.path,
                            workflow_run_id=workflow_group.workflow_run_id,
                            findings=(finding,),
                        )
                    )
                else:
                    comments.append(comment)

        if current_findings == 0:
            return None

        return GitHubReviewDraft(
            body=cls._build_review_body(
                pull_request=pull_request,
                mapped_count=len(comments),
                unmapped=unmapped,
            ),
            comments=tuple(comments),
        )

    @classmethod
    def _build_review_comment(
        cls,
        *,
        finding: Finding,
        changed_file: GitHubChangedFile | None,
        workflow_run_id: str,
        path: str,
    ) -> GitHubReviewComment | None:
        if changed_file is None or changed_file.patch is None:
            return None

        location = finding.location

        if location is None:
            return None

        line_hunks = cls._parse_right_side_lines(changed_file.patch)
        line_hunk = line_hunks.get(location.line)

        if line_hunk is None:
            return None

        start_line = location.start_line

        if start_line is not None:
            start_hunk = line_hunks.get(start_line)

            if start_hunk is None or start_hunk != line_hunk:
                return None

            if start_line == location.line:
                start_line = None

        return GitHubReviewComment(
            path=path,
            body=(
                f"**[{finding.severity}] {finding.category}** — `{finding.id}`\n\n"
                f"{finding.description}\n\n"
                f"Workflow run: `{workflow_run_id}`"
            ),
            line=location.line,
            side="RIGHT",
            start_line=start_line,
            start_side="RIGHT" if start_line is not None else None,
        )

    @staticmethod
    def _parse_right_side_lines(patch: str) -> dict[int, int]:
        """Return current-file line numbers present in each unified-diff hunk."""

        line_hunks: dict[int, int] = {}
        new_line: int | None = None
        hunk_number = 0

        for raw_line in patch.splitlines():
            if raw_line.startswith("@@ "):
                match = _HUNK_HEADER_RE.match(raw_line)

                if match is None:
                    return {}

                hunk_number += 1
                new_line = int(match.group("new_start"))
                continue

            if new_line is None or raw_line.startswith("\\"):
                continue

            prefix = raw_line[:1]

            if prefix in {" ", "+"}:
                line_hunks[new_line] = hunk_number
                new_line += 1
            elif prefix == "-":
                continue
            else:
                return {}

        return line_hunks

    @staticmethod
    def _build_review_body(
        *,
        pull_request: GitHubPullRequest,
        mapped_count: int,
        unmapped: list[GitHubWorkflowFindings],
    ) -> str:
        lines = [
            f"AI review for pull request #{pull_request.number}.",
        ]

        if mapped_count:
            lines.append(
                f"{mapped_count} finding(s) were mapped to inline review comments."
            )

        if unmapped:
            lines.extend(
                [
                    "",
                    "### Findings without a safe inline location",
                    "",
                    "The following findings could not be mapped to a changed line and ",
                    "are preserved here rather than attached to an arbitrary line:",
                ]
            )

            for workflow_group in unmapped:
                for finding in workflow_group.findings:
                    lines.append(
                        f"- **[{finding.severity}] {finding.category}** "
                        f"`{finding.id}` in `{workflow_group.path}` — "
                        f"{finding.description} "
                        f"(workflow run `{workflow_group.workflow_run_id}`)"
                    )

        return "\n".join(lines)
