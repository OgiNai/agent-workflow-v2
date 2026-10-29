"""API boundary tests for health and readiness endpoints."""

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from apps.main import code_app


def test_health() -> None:
    with TestClient(code_app) as client:
        response = client.get("/health")

    assert response.status_code == 200


def test_health_endpoint_is_live() -> None:
    with TestClient(code_app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_endpoint_reports_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "apps.api.health.check_readiness",
        AsyncMock(),
    )

    with TestClient(code_app) as client:
        response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "checks": {
            "config": "ok",
            "database": "ok",
        },
    }


def test_ready_endpoint_reports_missing_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from pydantic import ValidationError

    async def unavailable_config() -> None:
        raise ValidationError.from_exception_data(
            "AuthSettings",
            [
                {
                    "type": "missing",
                    "loc": ("api_token",),
                    "input": {},
                }
            ],
        )

    monkeypatch.setattr(
        "apps.api.health.check_readiness",
        unavailable_config,
    )

    with TestClient(code_app) as client:
        response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "checks": {
            "config": "incomplete",
            "database": "not_checked",
        },
    }
