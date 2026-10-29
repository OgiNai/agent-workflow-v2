"""API tests for the unified review workflow endpoint."""

from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from apps.core.security import verify_bearer_token
from apps.main import code_app
from apps.schemas.agent_outputs import EvaluatorOutput
from apps.schemas.responses import ReviewResponse


@pytest.fixture
def authenticated_client():
    async def bypass_auth() -> None:
        return None

    code_app.dependency_overrides[verify_bearer_token] = bypass_auth

    with TestClient(code_app) as client:
        yield client

    code_app.dependency_overrides.clear()


def make_response(*, status: str = "completed") -> ReviewResponse:
    return ReviewResponse(
        workflow_run_id=UUID("00000000-0000-0000-0000-000000000001"),
        status=status,
        task_type="review_refactor",
        source_type="inline_code",
        final_decision="pass" if status == "completed" else "failed",
        summary=(
            "Workflow completed successfully."
            if status == "completed"
            else "Workflow execution failed."
        ),
        final_code="def add(a, b):\n    return a + b\n",
        evaluation=EvaluatorOutput(
            final_decision="pass" if status == "completed" else "retry",
            rule_score=1.0,
            execution_score=1.0,
            llm_score=1.0,
            security_score=1.0,
            maintainability_score=1.0,
            correctness_score=1.0,
            final_score=1.0,
            findings=[],
            reasons=[],
            retry_feedback=None,
        ),
        artifacts=[],
        rounds_executed=1,
        steps=[],
    )


def test_create_review_requires_authentication(monkeypatch: pytest.MonkeyPatch):
    async def unexpected_workflow(*args, **kwargs):
        pytest.fail("workflow must not run when authentication fails")

    monkeypatch.setattr(
        "apps.api.reviews.run_code_workflow",
        unexpected_workflow,
    )

    with TestClient(code_app) as client:
        response = client.post(
            "/reviews",
            json={
                "instruction": "Review this function.",
                "code": "def add(a, b):\n    return a + b\n",
            },
        )

    assert response.status_code == 401


def test_create_review_rejects_invalid_request(authenticated_client):
    response = authenticated_client.post(
        "/reviews",
        json={
            "instruction": "Review this function.",
            "code": "def add(a, b):\n    return a + b\n",
            "file_path": "example.py",
        },
    )

    assert response.status_code == 422


def test_create_review_returns_completed_workflow(
    authenticated_client,
    monkeypatch: pytest.MonkeyPatch,
):
    workflow_result = make_response()

    workflow_mock = AsyncMock(return_value=workflow_result)
    monkeypatch.setattr(
        "apps.api.reviews.run_code_workflow",
        workflow_mock,
    )

    response = authenticated_client.post(
        "/reviews",
        json={
            "instruction": "Review this function.",
            "code": "def add(a, b):\n    return a + b\n",
            "save_artifacts": False,
        },
    )

    assert response.status_code == 202
    assert response.json()["status"] == "completed"
    assert response.json()["final_decision"] == "pass"

    workflow_mock.assert_awaited_once()


def test_create_review_returns_internal_server_error_for_failed_workflow(
    authenticated_client,
    monkeypatch: pytest.MonkeyPatch,
):
    workflow_result = make_response(status="failed")

    workflow_mock = AsyncMock(return_value=workflow_result)
    monkeypatch.setattr(
        "apps.api.reviews.run_code_workflow",
        workflow_mock,
    )

    response = authenticated_client.post(
        "/reviews",
        json={
            "instruction": "Review this function.",
            "code": "def add(a, b):\n    return a + b\n",
            "save_artifacts": False,
        },
    )

    assert response.status_code == 500
    assert response.json()["status"] == "failed"
    assert response.json()["summary"] == "Workflow execution failed."

    workflow_mock.assert_awaited_once()
