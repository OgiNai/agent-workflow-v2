"""OpenTelemetry configuration and workflow tracing."""

from __future__ import annotations

# from collections.abc import Awaitable, Callable
# from functools import wraps
from typing import ParamSpec, TypeVar  # Any

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import (
    TracerProvider,
)
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


'''
def trace_workflow(
    function: Callable[P, Awaitable[R]],
) -> Callable[P, Awaitable[R]]:
    """Trace a complete workflow execution."""

    @wraps(function)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        tracer = get_tracer("apps.workflows")
        request = kwargs.get("request")

        if request is None and args:
            request = args[0]

        attributes: dict[str, Any] = {
            "workflow.operation": function.__name__,
        }

        if request is not None:
            task_type = getattr(request, "task_type", None)
            if task_type is not None:
                attributes["workflow.request_task_type"] = task_type

            source_type = (
                "inline_code"
                if getattr(request, "code", None)
                else "file_path"
                if getattr(request, "file_path", None)
                else "none"
            )
            attributes["workflow.request_source_type"] = source_type

            max_rounds = getattr(request, "max_rounds", None)
            if max_rounds is not None:
                attributes["workflow.max_rounds"] = max_rounds

        with tracer.start_as_current_span(
            "workflow.run",
            kind=SpanKind.INTERNAL,
            attributes=attributes,
        ) as span:
            try:
                result = await function(*args, **kwargs)

                workflow_id = getattr(result, "workflow_run_id", None)
                if workflow_id is not None:
                    span.set_attribute(
                        "workflow.id",
                        str(workflow_id),
                    )

                status = getattr(result, "status", None)
                if status is not None:
                    span.set_attribute(
                        "workflow.status",
                        status,
                    )

                final_decision = getattr(
                    result,
                    "final_decision",
                    None,
                )
                if final_decision is not None:
                    span.set_attribute(
                        "workflow.final_decision",
                        final_decision,
                    )

                rounds = getattr(
                    result,
                    "rounds_executed",
                    None,
                )
                if rounds is not None:
                    span.set_attribute(
                        "workflow.rounds_executed",
                        rounds,
                    )

                if status == "failed":
                    span.set_status(
                        Status(
                            StatusCode.ERROR,
                            "Workflow returned failed status.",
                        )
                    )
                else:
                    span.set_status(Status(StatusCode.OK))

                return result

            except Exception as exc:
                span.record_exception(exc)
                span.set_status(
                    Status(
                        StatusCode.ERROR,
                        str(exc),
                    )
                )
                raise

    return wrapper
'''
