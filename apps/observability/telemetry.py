"""OpenTelemetry configuration and workflow tracing."""

from __future__ import annotations

# from collections.abc import Awaitable, Callable
# from functools import wraps
from typing import ParamSpec, TypeVar  # Any

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)

# from opentelemetry.trace import SpanKind, Status, StatusCode
from apps.core.settings import get_telemetry_settings

P = ParamSpec("P")
R = TypeVar("R")

_tracer_provider: TracerProvider | None = None


def initialize_telemetry() -> None:
    """Initialize the OpenTelemetry tracer provider once per process."""
    global _tracer_provider

    if _tracer_provider is not None:
        return

    settings = get_telemetry_settings()

    resource = Resource.create(
        {
            "service.name": settings.otel_service_name,
        }
    )

    provider = TracerProvider(resource=resource)

    if settings.otel_exporter_otlp_endpoint:
        exporter = OTLPSpanExporter(
            endpoint=settings.otel_exporter_otlp_endpoint,
        )
        provider.add_span_processor(BatchSpanProcessor(exporter))

    elif settings.otel_console_exporter:
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)
    _tracer_provider = provider


def get_tracer(name: str) -> trace.Tracer:
    """Return an application tracer."""
    return trace.get_tracer(name)


def shutdown_telemetry() -> None:
    """Flush and shut down OpenTelemetry exporters."""
    if _tracer_provider is not None:
        _tracer_provider.shutdown()
