# Milestone 3 — Observability

**Goal:** Make workflow execution observable, traceable, and measurable.

## 3.1 — Structured Logging

Implement structured JSON logging.

Include useful correlation information such as:

* Workflow ID.
* Agent name.
* Step name.
* Round number.
* Event type.
* Error information where appropriate.

Do not log secrets or sensitive source content unnecessarily.

## 3.2 — OpenTelemetry Foundation

Introduce OpenTelemetry with configurable exporters.

Telemetry must be optional and configurable.

## 3.3 — Workflow and Agent Spans

Create telemetry hierarchy:

```text
Workflow Span
    ├── Router Span
    ├── Planner Span
    ├── Agent Span
    │     └── LLM Span
    ├── Tool Span
    ├── Test Runner Span
    └── Evaluator Span
```

The telemetry model is distinct from persisted workflow history.

Persistence answers:

> What happened in the workflow?

Telemetry answers:

> How did the workflow execute?

## 3.4 — LLM Usage Tracking

Track LLM usage where supported:

* Input tokens.
* Output tokens.
* Total tokens.
* Model.
* Latency.

Persist usage on agent steps where appropriate.

Expose usage through telemetry without exposing sensitive prompt content.

## 3.5 — Prompt Versioning

Version prompts explicitly.

Persist the prompt version associated with LLM agent execution.

**Outcome:** Workflow behavior can be monitored, diagnosed, and measured.