import pytest
import os
from solution import get_api_key, get_headers

def test_get_api_key_success(monkeypatch):
    monkeypatch.setenv("API_KEY", "test_secret_123")
    assert get_api_key() == "test_secret_123"

def test_get_api_key_missing():
    if "API_KEY" in os.environ:
        del os.environ["API_KEY"]
    with pytest.raises(EnvironmentError, match="API_KEY environment variable is not set."):
        get_api_key()

def test_get_headers_success(monkeypatch):
    monkeypatch.setenv("API_KEY", "secret_token")
    expected = {"Authorization": "Bearer secret_token"}
    assert get_headers() == expected

def test_get_headers_failure():
    if "API_KEY" in os.environ:
        del os.environ["API_KEY"]
    with pytest.raises(EnvironmentError):
        get_headers()