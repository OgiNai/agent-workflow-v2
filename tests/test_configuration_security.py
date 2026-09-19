"""Tests for configuration secret handling at application boundaries."""

from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from apps.core.security import verify_bearer_token
from apps.core.settings import AuthSettings
from apps.llm.gemini_client import (
    LLMSettings,
    _get_gemini_client,
    genai,
)

SECRET_API_TOKEN = "api-token-secret-for-test"
SECRET_GEMINI_KEY = "gemini-api-key-secret-for-test"
SECRET_DATABASE_URL = (
    "postgresql+asyncpg://test-user:database-password-secret@example.internal:5432/test"
)


def make_auth_settings() -> AuthSettings:
    return AuthSettings(
        app_env="test",
        api_token=SECRET_API_TOKEN,
        gemini_api_key=SECRET_GEMINI_KEY,
        database_url=SECRET_DATABASE_URL,
        debug=False,
        project_path="/tmp/project",
    )


@pytest.mark.parametrize("representation", [repr, str])
def test_secret_settings_are_masked_in_string_representations(
    representation,
) -> None:
    settings = make_auth_settings()

    rendered = representation(settings)

    assert SECRET_API_TOKEN not in rendered
    assert SECRET_GEMINI_KEY not in rendered
    assert SECRET_DATABASE_URL not in rendered
    assert "**********" in rendered


@pytest.mark.anyio
async def test_authentication_does_not_log_api_token(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    settings = make_auth_settings()

    monkeypatch.setattr(
        "apps.core.security.get_auth_settings",
        lambda: settings,
    )

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="wrong-token",
    )

    with caplog.at_level("INFO"), pytest.raises(HTTPException):
        await verify_bearer_token(credentials)

    assert SECRET_API_TOKEN not in caplog.text


def test_llm_client_does_not_log_api_key(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    settings = make_auth_settings()

    monkeypatch.setattr(
        "apps.llm.gemini_client.get_auth_settings",
        lambda: settings,
    )

    fake_client = Mock()
    fake_client.aio.aclose = AsyncMock()
    captured_api_key = None

    def fake_client_factory(*, http_options, api_key):
        nonlocal captured_api_key
        captured_api_key = api_key
        return fake_client

    monkeypatch.setattr(
        genai,
        "Client",
        fake_client_factory,
    )

    try:
        with caplog.at_level("INFO"):
            result = _get_gemini_client(
                LLMSettings(
                    initial_delay=1,
                    attempts=1,
                    model_name="test-model",
                    temperature=0,
                )
            )

        assert result is fake_client
        assert captured_api_key == SECRET_GEMINI_KEY
        assert SECRET_GEMINI_KEY not in caplog.text
    finally:
        monkeypatch.setattr("apps.llm.gemini_client._client", None)


@pytest.mark.anyio
async def test_configuration_secrets_do_not_reach_api_error_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Public API failure responses expose controlled descriptions only."""

    from uuid import UUID

    from fastapi.testclient import TestClient

    from apps.core.security import verify_bearer_token
    from apps.main import code_app
    from apps.schemas.responses import ReviewResponse

    async def bypass_auth() -> None:
        return None

    response_model = ReviewResponse(
        workflow_run_id=UUID("00000000-0000-0000-0000-000000000002"),
        status="failed",
        task_type="review_refactor",
        source_type="inline_code",
        final_decision="failed",
        summary="Workflow execution failed.",
        final_code=None,
        evaluation=None,
        artifacts=[],
        rounds_executed=1,
        steps=[],
    )

    async def fake_workflow(*args, **kwargs):
        return response_model

    code_app.dependency_overrides[verify_bearer_token] = bypass_auth
    monkeypatch.setattr(
        "apps.api.reviews.run_code_workflow",
        fake_workflow,
    )

    try:
        with TestClient(code_app) as client:
            response = client.post(
                "/reviews",
                json={
                    "instruction": "Review this function.",
                    "code": "def add(a, b): return a + b",
                },
            )
    finally:
        code_app.dependency_overrides.clear()

    assert response.status_code == 500
    assert SECRET_API_TOKEN not in response.text
    assert SECRET_GEMINI_KEY not in response.text
    assert SECRET_DATABASE_URL not in response.text


@pytest.mark.anyio
async def test_persisted_workflow_state_does_not_expose_configuration_secrets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from unittest.mock import AsyncMock

    from apps.agents.inspection_agent import InspectionAgent
    from apps.agents.planner_agent import PlannerAgent
    from apps.core.constants import DEFAULT_MAX_ROUNDS
    from apps.core.workflow_config import WorkflowConfig
    from apps.database.session import close_database_engine
    from apps.database.unit_of_work import UnitOfWork
    from apps.schemas.agent_outputs import PlannerOutput
    from apps.schemas.requests import ReviewRequest
    from apps.workflows.code_workflow import CodeWorkflow

    planner = Mock(spec=PlannerAgent)
    planner.run = AsyncMock(
        return_value=(
            PlannerOutput(
                task_type="review_refactor",
                requires_generation=False,
                requires_refactor=True,
                requires_tests=True,
            ),
            5,
        )
    )

    inspector = Mock(spec=InspectionAgent)
    inspector.run = AsyncMock(
        side_effect=RuntimeError(f"database failure involving {SECRET_DATABASE_URL}")
    )

    workflow = CodeWorkflow(
        planner=planner,
        inspector=inspector,
        config=WorkflowConfig(
            max_rounds=DEFAULT_MAX_ROUNDS,
            force_retry_rounds=0,
            always_retry=False,
        ),
    )

    try:
        result = await workflow.run(
            ReviewRequest(
                instruction="Review this function.",
                code="def add(a, b): return a + b",
            )
        )

        async with UnitOfWork() as uow:
            persisted_workflow = await uow.workflows.get(
                result.workflow_run_id,
            )
            persisted_steps = await uow.agent_steps.list_by_workflow(
                result.workflow_run_id,
            )

        assert persisted_workflow is not None
        assert persisted_workflow.summary == "Workflow execution failed."

        persisted_text = repr(persisted_workflow)

        for step in persisted_steps:
            persisted_text += repr(step)

        assert SECRET_API_TOKEN not in persisted_text
        assert SECRET_GEMINI_KEY not in persisted_text
        assert SECRET_DATABASE_URL not in persisted_text
    finally:
        await close_database_engine()


def test_benchmark_report_does_not_expose_sensitive_input() -> None:
    from datetime import UTC, datetime
    from pathlib import Path
    from uuid import uuid4

    from apps.evals.benchmark_runner import build_benchmark_report
    from apps.schemas.benchmark import BenchmarkCaseResult
    from apps.schemas.responses import ReviewResponse
    from apps.schemas.workflow import WorkflowStepTrace

    secret = SECRET_GEMINI_KEY

    response = ReviewResponse(
        workflow_run_id=uuid4(),
        status="completed",
        task_type="review_refactor",
        source_type="inline_code",
        final_decision="pass",
        summary="Completed.",
        final_code="def example():\n    return 1\n",
        steps=[
            WorkflowStepTrace(
                step_name="reviewer",
                step_type="agent",
                status="success",
                metadata={
                    "internal_configuration_value": secret,
                },
            )
        ],
        rounds_executed=1,
    )

    result = BenchmarkCaseResult(
        case_id="secret-test",
        case_version="1",
        category="correctness",
        workflow_run_id=response.workflow_run_id,
        response=response,
        finding_matches=[],
    )

    report = build_benchmark_report(
        results=[result],
        benchmark_run_id=uuid4(),
        started_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
        cases_path=Path("benchmarks/cases"),
    )

    serialized = report.model_dump_json()

    assert secret not in serialized
