"""Tests for telemetry configuration and initialization."""

import pytest

from apps.core.settings import TelemetrySettings
from apps.observability import telemetry


def test_telemetry_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    settings = TelemetrySettings(_env_file=None)

    assert settings.otel_service_name == "agent-workflow-v2"
    assert settings.otel_exporter_otlp_endpoint is None
    assert settings.otel_console_exporter is False


@pytest.mark.parametrize(
    ("field", "value"),
    [
        (
            "otel_exporter_otlp_endpoint",
            "http://localhost:4318/v1/traces",
        ),
        (
            "otel_console_exporter",
            True,
        ),
    ],
)
def test_telemetry_settings_accept_explicit_configuration(
    field: str,
    value: str | bool,
) -> None:
    settings = TelemetrySettings(
        _env_file=None,
        **{field: value},
    )

    assert getattr(settings, field) == value


def test_telemetry_records_service_name_without_otlp_endpoint_attribute(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = TelemetrySettings(
        _env_file=None,
        otel_service_name="test-service",
        otel_exporter_otlp_endpoint="https://otel.example.internal/v1/traces",
    )

    captured_provider = None

    def capture_provider(provider) -> None:
        nonlocal captured_provider
        captured_provider = provider

    monkeypatch.setattr(
        telemetry,
        "_tracer_provider",
        None,
    )
    monkeypatch.setattr(
        telemetry,
        "get_telemetry_settings",
        lambda: settings,
    )
    monkeypatch.setattr(
        telemetry.trace,
        "set_tracer_provider",
        capture_provider,
    )

    telemetry.initialize_telemetry()

    assert captured_provider is not None

    attributes = captured_provider.resource.attributes

    assert attributes["service.name"] == "test-service"
    assert settings.otel_exporter_otlp_endpoint not in attributes.values()

    telemetry._tracer_provider = None
