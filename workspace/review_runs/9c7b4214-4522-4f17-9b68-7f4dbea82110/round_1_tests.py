import pytest
import os
from solution import get_api_key, get_headers

def test_get_api_key_success(monkeypatch):
    monkeypatch.setenv("API_KEY", "test_secret_key")
    assert get_api_key() == "test_secret_key"

def test_get_api_key_missing(monkeypatch):
    monkeypatch.delenv("API_KEY", raising=False)
    with pytest.raises(EnvironmentError, match="The API_KEY environment variable is not set."):
        get_api_key()

def test_get_headers_success(monkeypatch):
    monkeypatch.setenv("API_KEY", "my_token")
    expected = {"Authorization": "Bearer my_token"}
    assert get_headers() == expected

def test_get_headers_failure(monkeypatch):
    monkeypatch.delenv("API_KEY", raising=False)
    with pytest.raises(EnvironmentError):
        get_headers()