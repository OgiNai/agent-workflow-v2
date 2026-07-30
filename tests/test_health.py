from fastapi.testclient import TestClient

from apps.main import code_app


def test_health() -> None:
    with TestClient(code_app) as client:
        response = client.get("/health")

    assert response.status_code == 200