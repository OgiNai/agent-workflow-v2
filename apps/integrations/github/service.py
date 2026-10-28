"""Orchestration service for GitHub pull-request reviews."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from apps.integrations.github.adapter import GitHubAdapter
from apps.integrations.github.client import GitHubRESTClient
from apps.integrations.github.models import GitHubWorkflowFindings
from apps.schemas.requests import ReviewRequest
from apps.schemas.responses import (
    GitHubFileWorkflowResult,
    GitHubPullRequestReviewResponse,
    ReviewResponse,
)
from apps.workflows.code_workflow import run_code_workflow

WorkflowRunner = Callable[[ReviewRequest], Awaitable[ReviewResponse]]


class GitHubPRReviewService:
    """Coordinate file-level workflows and publish one aggregate PR review."""

    def __init__(
        self,
        client: GitHubRESTClient,
        *,
        workflow_runner: WorkflowRunner = run_code_workflow,
    ) -> None:
        self.client = client
        self.adapter = GitHubAdapter(client)
        self.workflow_runner = workflow_runner

    async def review_pull_request(
        self,
        *,
        owner: str,
        repository_name: str,
        pull_request_number: int,
    ) -> GitHubPullRequestReviewResponse:
        """Review supported files and publish findings against the PR head SHA."""
        repository = await self.client.get_repository(
            owner=owner,
            repository_name=repository_name,
        )
        pull_request = await self.client.get_pull_request(
            repository=repository,
            pull_request_number=pull_request_number,
        )
        changed_files = await self.client.list_pull_request_files(pull_request)

        file_requests = await self.adapter.build_file_review_requests(
            pull_request,
            changed_files=changed_files,
        )

        workflow_results: list[GitHubFileWorkflowResult] = []
        workflow_findings: list[GitHubWorkflowFindings] = []
        workflow_failed = False

        for file_request in file_requests:
            result = await self.workflow_runner(file_request.request)

            workflow_results.append(
                GitHubFileWorkflowResult(
                    path=file_request.path,
                    workflow_run_id=result.workflow_run_id,
                    status=result.status,
                    final_decision=result.final_decision,
                    summary=result.summary,
                )
            )

            if result.status == "failed":
                workflow_failed = True
                continue

            findings = (
                tuple(result.evaluation.findings)
                if result.evaluation is not None
                else ()
            )
            workflow_findings.append(
                GitHubWorkflowFindings(
                    path=file_request.path,
                    workflow_run_id=result.workflow_run_id,
                    findings=findings,
                )
            )

        if workflow_failed:
            return GitHubPullRequestReviewResponse(
                repository=repository.full_name,
                pull_request_number=pull_request.number,
                head_sha=pull_request.head_sha,
                status="failed",
                workflows=workflow_results,
                github_review_id=None,
            )

        review_id = await self.adapter.publish_pull_request_review(
            pull_request=pull_request,
            changed_files=changed_files,
            workflow_findings=workflow_findings,
        )

        return GitHubPullRequestReviewResponse(
            repository=repository.full_name,
            pull_request_number=pull_request.number,
            head_sha=pull_request.head_sha,
            status="completed",
            workflows=workflow_results,
            github_review_id=review_id,
        )
