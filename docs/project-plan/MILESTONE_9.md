# Milestone 9 — OpenTelemetry Collector and Trace Backend

Set up a complete OTLP telemetry pipeline so the OpenTelemetry instrumentation implemented in Milestone 3 has a real destination.

## 9.1 — Define the telemetry architecture

- Decide on the production telemetry pipeline:
  - Application → OTLP → OpenTelemetry Collector → trace backend
- Document the role of each component.
- Keep application instrumentation independent from the specific telemetry backend.
- Define separate development and production telemetry configurations.

## 9.2 — Add local OpenTelemetry Collector

- Add an OpenTelemetry Collector configuration for local development.
- Configure the Collector to receive OTLP over HTTP on port `4318`.
- Configure a development trace exporter/backend.
- Verify that application spans are successfully received by the Collector.
- Verify that the existing `localhost:4318` exporter warnings disappear.

## 9.3 — Select and configure the production trace backend

- Select a production-compatible tracing backend compatible with the project's free-tier constraints.
- Configure the OpenTelemetry Collector to export traces to the selected backend.
- Store backend credentials/configuration through environment variables or deployment secrets.
- Do not hard-code telemetry credentials or endpoints.

## 9.4 — Configure application telemetry endpoints

- Add explicit telemetry configuration to application settings.
- Support separate development and production OTLP endpoints.
- Avoid attempting to export to `localhost:4318` when running in the production environment.
- Define appropriate exporter behavior when telemetry is unavailable.
- Ensure telemetry failures do not cause workflow execution failures.

## 9.5 — Deploy the telemetry pipeline

- Deploy the application and telemetry components using the chosen production architecture.
- Configure the production OTLP endpoint.
- Verify network connectivity between the application, Collector, and backend.
- Verify that traces from deployed workflow executions reach the backend.

## 9.6 — Validate end-to-end tracing

Run a complete workflow and verify:

- One workflow/root span is created.
- Agent/tool child spans are created.
- Trace context is propagated across the workflow.
- Spans contain the expected workflow/run identifiers.
- Trace status correctly reflects successful and failed executions.
- Multiple workflow executions produce distinct traces.
- Telemetry export failures do not affect API responses or workflow execution.

## 9.7 — Production telemetry hardening

- Configure batching and retry behavior.
- Define appropriate exporter timeouts.
- Prevent excessive telemetry retry logging.
- Ensure graceful shutdown flushes pending spans where practical.
- Review sensitive-data handling in span attributes and events.
- Ensure API keys, prompts, source code, and other sensitive values are not unintentionally exported.
- Document telemetry failure/degradation behavior.
