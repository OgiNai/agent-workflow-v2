# AI Code Review & Refactoring Platform

## Purpose

Build a production-quality AI Code Review & Refactoring Platform that demonstrates real-world AI Engineering practices rather than simply wrapping an LLM API.

The project serves two purposes:

1. Learn how modern AI agent systems are designed and implemented.
2. Produce a portfolio project suitable for Junior AI Engineer / ML Engineer applications.

---

# Project Goals

The project should demonstrate:

- Multi-agent orchestration
- Structured LLM outputs
- Deterministic tools
- Production architecture
- Evaluation pipeline
- Observability
- PostgreSQL persistence
- Docker deployment
- CI/CD
- Cloud deployment
- Extensibility

The focus is engineering quality, maintainability and architecture rather than model performance.

---

# Technology Stack

## Backend

- Python 3.11+
- FastAPI
- Pydantic v2

## LLM

- Google Gemini
- Native async SDK
- Structured JSON responses

## Database

- Neon PostgreSQL

## Deployment

- Docker
- GitHub Actions
- Google Cloud Run
- Azure (later)

## UI

- API first
- Streamlit dashboard (later)

---

# Architecture Principles

The project should always follow these principles.

- Production-oriented
- Async-first
- Strong typing
- Dependency Injection
- Modular
- Deterministic where possible
- Easy to extend
- Testable
- Single Responsibility Principle

---

# Dependency Direction

All dependencies should point in one direction only.

```
core
↑
schemas
↑
tools
↑
agents
↑
workflows
↑
api
↑
main
```

Nothing should import upward.

`main.py` is the application composition root.

---

# Workflow Overview

The system supports two scenarios.

## Scenario A — Feature Generation

User provides:

- natural-language instruction

Workflow

```
Planner
        │
        ▼
CodeWriter (generate)
        │
        ▼
Reviewer
        ▼
Security Auditor
        ▼
CodeWriter (refactor)
        ▼
Test Generator
        ▼
Test Executor
        ▼
Evaluator
```

If evaluation returns `retry`, execution continues with

```
Reviewer
    ▼
Security Auditor
    ▼
CodeWriter (refactor)
    ▼
Test Generator
    ▼
Test Executor
    ▼
Evaluator
```

until

- pass
- pass_with_warnings
- retry limit reached

---

## Scenario B — Code Review & Refactoring

User provides

- inline code

or

- file path

Workflow

```
Planner
        │
        ▼
Reviewer
        ▼
Security Auditor
        ▼
CodeWriter (refactor)
        ▼
Test Generator
        ▼
Test Executor
        ▼
Evaluator
```

Uses the same retry loop.

---

# Agents

## PlannerAgent

Responsibilities

- understand user request
- decide workflow
- generate execution plan

---

## InspectionAgent

Single implementation.

Supports two modes.

- reviewer
- security_auditor

---

## CodeWriterAgent

Single implementation.

Supports two modes.

- generate
- refactor

---

## TestGeneratorAgent

Generates pytest tests.

---

## EvaluatorAgent

Responsible only for evaluating the current candidate.

Returns

- pass
- pass_with_warnings
- retry

The Evaluator never

- knows retry limits
- terminates the workflow
- returns fail

Those responsibilities belong to the workflow orchestrator.

---

# Workflow Orchestrator

Responsible for

- retry loop
- max rounds
- workflow state
- final workflow status

If retry limit is reached

```
status = completed_with_warnings
final_decision = unresolved
```

Infrastructure failures produce

```
status = failed
```

Examples

- database failure
- API failure
- internal exception

---

# API Design

## Request

Every request always contains

```
instruction
```

Optionally

```
code
```

or

```
file_path
```

Code and file path are mutually exclusive.

---

## Task Types

```
auto
generate
review_refactor
```

Auto resolves to

```
if source code exists
    review_refactor

otherwise
    generate
```

---

## Source Types

Internal only.

```
none
inline_code
file_path
```

The client never specifies source type.

---

# Router Responsibilities

The router

- validates request
- loads file when necessary
- strips markdown fences
- resolves source type
- resolves automatic task type

It does not perform AI reasoning.

---

# File System

Shared helper

```
apps/tools/file_path_helpers.py
```

Provides

- project root
- safe project path resolution
- artifact path resolution
- workspace helpers

All file operations use these helpers.

Artifacts are stored only inside

```
workspace/review_runs/{workflow_run_id}
```

---

# Gemini Client

Uses native async SDK.

Lazy singleton.

```
_get_gemini_client()
```

Cleanup

```
close_gemini_client()
```

called from FastAPI lifespan.

---

# FastAPI Lifecycle

Startup

- no initialization

Shutdown

- close Gemini client

Later

- database pool
- telemetry

---

# Test Runner

Deterministic tool.

Not an agent.

Executes pytest asynchronously.

Returns structured results.

---

# Evaluation

Three evaluation systems are used.

## Rule-based evaluation

Static deterministic checks.

---

## Execution evaluation

Generated tests.

Pytest execution.

---

## LLM evaluation

LLM-as-a-judge.

The Evaluator combines all three into the final decision.

---

# Database

Current schema

- workflow_runs
- agent_steps
- tool_calls
- artifacts
- feedback

Event sourcing may be added later.

---

# Coding Standards

- Async wherever practical
- Dependency Injection
- Pydantic models
- Structured outputs
- Type hints everywhere
- Small focused modules
- No duplicated agents
- Prefer modes over duplicated implementations

---

# Milestone 1 — Core Workflow

**Goal:** Establish the initial end-to-end AI code review/refactoring workflow.

## 1.1 — Project Foundation

* Establish Python project structure.
* Configure dependency management with `uv`.
* Configure linting and formatting.
* Configure pytest.
* Establish application entry point.
* Establish environment configuration.
* Establish initial API structure.

## 1.2 — Workflow Input

Support:

* User instruction.
* Inline source code.
* File path input.

`code` and `file_path` are mutually exclusive.

Define the initial task types:

```text
auto
generate
review_refactor
```

## 1.3 — Router

Implement deterministic routing based on the request.

Responsibilities:

* Validate input.
* Determine source type.
* Resolve `auto` task type.
* Produce a structured `RouterResult`.

The router must not perform LLM reasoning.

## 1.4 — Planner

Implement the initial deterministic Planner.

Responsibilities:

* Determine required workflow stages.
* Determine whether initial code generation is required.
* Produce a structured `WorkflowPlan`.

The Planner does not execute agents.

The Planner remains deterministic because the initial workflow has a fixed set of capabilities and a predictable execution path.

## 1.5 — Code Writer

Implement the CodeWriter agent with explicit modes:

```text
generate
refactor
repair
```

Use structured LLM output.

## 1.6 — Code Reviewer

Implement the Reviewer agent.

Responsibilities:

* Analyze source code.
* Identify correctness and maintainability issues.
* Produce structured findings.

## 1.7 — Security Auditor

Implement a separate Security Auditor agent.

Responsibilities:

* Analyze security risks.
* Identify unsafe patterns.
* Produce structured findings.

## 1.8 — Test Generator

Implement the Test Generator agent.

Responsibilities:

* Generate tests based on the candidate code and workflow context.
* Produce executable test artifacts.

## 1.9 — Test Runner

Execute generated tests through a controlled subprocess.

Capture:

* Exit code.
* Standard output.
* Standard error.
* Test results.

## 1.10 — Evaluator

Implement deterministic and LLM-assisted evaluation.

The evaluator combines:

* Review findings.
* Security findings.
* Test execution.
* Candidate code.
* Evaluation criteria.

The evaluator produces a structured decision.

## 1.11 — Workflow Orchestration

Implement the end-to-end workflow:

```text
Request
  ↓
Router
  ↓
Planner
  ↓
[CodeWriter.generate]
  ↓
Reviewer
  ↓
Security Auditor
  ↓
CodeWriter.refactor/repair
  ↓
Test Generator
  ↓
Test Runner
  ↓
Evaluator
  ↓
Retry or Complete
```

For review/refactor requests, the initial generation stage is skipped.

On retry:

```text
Evaluator
   ↓
Reviewer
   ↓
Security Auditor
   ↓
CodeWriter
```

## 1.12 — API

Implement the initial review API.

Support:

* Authentication.
* Review requests.
* Workflow execution.
* Structured responses.

**Outcome:** A complete local end-to-end workflow exists.

---

# Milestone 2 — Persistence and Application State

**Goal:** Persist workflow execution and expose durable application state.

## 2.1 — Persistence Foundation

* Introduce PostgreSQL.
* Configure Neon PostgreSQL.
* Add SQLAlchemy.
* Add async database access.
* Establish database models.
* Introduce Alembic.

Core entities:

```text
workflow_runs
agent_steps
tool_calls
artifacts
feedback
```

## 2.2 — Repository Layer

Implement repositories for persistence operations.

Repositories must isolate database access from workflow and agent logic.

Use dependency injection.

## 2.3 — Persistence Integration

Persist:

* Workflow runs.
* Agent execution.
* Tool execution.
* Generated artifacts.
* Evaluation results.
* Workflow status.

Use Alembic migrations as the schema authority.

Do not create database tables automatically during application startup.

## 2.4 — Feedback API

Implement:

```text
POST /reviews/{workflow_run_id}/feedback
```

Feedback contains:

* `rating`
* `accepted`
* `comment`

One feedback record exists per workflow.

A subsequent submission overwrites the existing feedback.

## 2.5 — Database Bootstrap and Readiness

Implement application startup/readiness checks.

Startup must verify:

* Configuration validity.
* Database connectivity.

The `/ready` endpoint must expose readiness information without leaking secrets.

Database cleanup must occur during application shutdown.

**Outcome:** Workflow state survives process restarts and can be inspected through persisted data.

---

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

---

# Milestone 4 — Evaluation and Benchmarking

**Goal:** Establish objective evaluation and regression measurement for the AI workflow.

## 4.1 — Normalized Findings

Create a canonical finding representation.

Each finding should include:

* Stable application-generated finding ID.
* Severity.
* Category.
* Message.
* File path where applicable.
* Line information where applicable.
* Source agent.
* Resolution status.

Reviewer and Security Auditor findings begin as unresolved.

The Evaluator determines whether findings are resolved after refactoring.

Findings remain persisted through existing `AgentStep.output_json`; a separate findings table is not required.

## 4.2 — Structured Test Results

Standardize pytest execution results.

Use `pytest-json-report` where appropriate.

Define a canonical `TestRunResult` containing information such as:

* Test count.
* Passed.
* Failed.
* Skipped.
* Errors.
* Exit status.
* Duration.

## 4.3 — Deterministic Evaluation

Implement deterministic scoring and decision policy.

Evaluation should combine:

* Rule/evaluation score.
* Test execution score.
* Severity penalties.
* Finding resolution.

The LLM evaluator may assess qualitative dimensions such as:

* Correctness.
* Security.
* Maintainability.
* Finding resolution.

Deterministic application logic owns:

* Rule score.
* Execution score.
* Severity penalties.
* Final score.
* Final decision.
* Retry policy.

High/critical unresolved findings can force retry.

Failed test execution can force retry.

## 4.4 — Benchmark Corpus

Create a representative benchmark corpus covering:

* Correctness issues.
* Security issues.
* Maintainability issues.
* Refactoring tasks.
* Feature-generation tasks.
* Test-generation scenarios.
* Difficult edge cases.

## 4.5 — Benchmark Reports

Generate reports measuring:

* Evaluation score.
* Correctness.
* Security.
* Maintainability.
* Test success.
* Finding resolution.
* Retry rate.
* Latency.
* Token usage.

## 4.6 — Metrics Storage

Introduce dedicated metrics storage only when a concrete query/reporting requirement justifies it.

Avoid duplicating information already available through workflow history and telemetry.

## 4.7 — Comparison Tooling

Provide tooling for comparing:

* Model versions.
* Prompt versions.
* Workflow configurations.
* Agent behavior.

**Outcome:** The platform can objectively measure workflow quality and detect regressions.

---

# Milestone 5 — Production Hardening

**Goal:** Harden the existing workflow into a reliable production-oriented application before adding external integrations or deployment complexity.

The deterministic Planner remains the default. The application owns workflow orchestration, retry behavior, safety policies, and execution control. LLM agents remain responsible for task-specific reasoning within their specialized roles.

## 5.1 — Workflow State, Contracts and Orchestration

Review and harden the boundaries between:

```text
API
 ↓
Router
 ↓
Planner
 ↓
CodeWorkflow
 ↓
Agents / Tools
 ↓
Evaluator
 ↓
Persistence
```

* Review all workflow state models and contracts.
* Eliminate duplicated or ambiguous state.
* Make workflow state transitions explicit.
* Verify dependency direction.
* Verify dependency injection boundaries.
* Ensure the orchestrator remains responsible for workflow control.
* Ensure agents do not mutate orchestration state directly.
* Wire request-level workflow configuration consistently.
* Verify `max_rounds` and retry configuration behavior.
* Verify both generation and review/refactor paths.
* Verify retry always returns to Reviewer → Security Auditor before refactoring.

## 5.2 — Failure Handling and Resilience

Define and test controlled behavior for:

* LLM timeout.
* LLM provider/API failure.
* Malformed structured LLM responses.
* Database connection/query failure.
* File access failure.
* Test execution failure.
* Evaluator failure.
* Unexpected agent exceptions.
* Workflow retry exhaustion.

Define clear distinctions between:

```text
Infrastructure / application failure
    → status = failed

Evaluation failure requiring another attempt
    → workflow retry

Retry limit reached
    → status = completed_with_warnings
       final_decision = unresolved
```

* Ensure exceptions are logged and traced appropriately.
* Prevent infrastructure failures from being misclassified as evaluation failures.
* Ensure partial workflow failures leave consistent persisted state.
* Add automated tests for all important failure paths.

## 5.3 — Automated Testing Strategy

Establish a comprehensive testing pyramid:

```text
             E2E
              │
        Integration
              │
       Workflow / Agent
              │
             Unit
```

Add or improve tests for:

* Router behavior.
* Planner behavior.
* Agent contracts.
* Repository operations.
* Evaluation logic.
* Retry policy.
* Persistence.
* API endpoints.
* File handling.
* Failure scenarios.
* Workflow integration.

Use dependency injection to test workflows without making real LLM calls.

The complete test suite must be deterministic and runnable without external LLM access where practical.

## 5.4 — Configuration and Environment Hardening

Review and harden:

* Pydantic settings validation.
* Development/test/production configuration.
* Workflow configuration.
* LLM configuration.
* Database configuration.
* Telemetry configuration.
* API authentication configuration.

Ensure secrets and sensitive configuration values never appear in:

* Logs.
* OpenTelemetry attributes.
* API responses.
* Persisted workflow data.
* Benchmark reports.
* Error messages.

## 5.5 — Security Hardening

Review the application for security risks associated with API access, filesystem access, and generated-code execution.

Cover:

* API authentication.
* Request validation and size limits.
* Path traversal prevention.
* Workspace isolation.
* Artifact path safety.
* Generated-code execution boundaries.
* Pytest/subprocess execution boundaries.
* Malicious source-code input.
* Prompt injection through source code and comments.
* Secret leakage.
* Unsafe error disclosure.

Document known security limitations of executing generated Python code.

## 5.6 — Production Readiness Validation

Run a complete production-readiness check covering:

* Full automated test suite.
* Benchmark suite.
* Linting.
* Type checking.
* Database migration validation.
* Clean application startup.
* Clean application shutdown.
* Database connectivity.
* LLM failure handling.
* Retry behavior.
* Persistence consistency.
* OpenTelemetry traces.
* Structured logs.

**Outcome:** The application has a stable, tested and observable local production baseline suitable for external integration and deployment.

---

# Milestone 6 — GitHub Integration

**Goal:** Integrate GitHub as an external adapter while keeping GitHub-specific concerns isolated from the core workflow and domain logic.

## 6.1 — GitHub Integration Architecture

* Define GitHub as an external adapter around the existing workflow.
* Keep `CodeWorkflow` independent of GitHub APIs.
* Define the boundary between:

  * GitHub repository data.
  * Application/domain models.
  * `ReviewRequest`.
  * `ReviewResponse`.
* Define which GitHub operations belong to the MVP.
* Defer non-essential GitHub functionality.
* Define security and permission boundaries before implementation.

Target architecture:

```text
GitHub Adapter
      ↓
ReviewRequest
      ↓
CodeWorkflow
      ↓
ReviewResponse
      ↓
GitHub Adapter
```

## 6.2 — GitHub Authentication

* Select the authentication mechanism appropriate for the MVP.
* Store GitHub credentials using the existing configuration and secret-management approach.
* Never expose credentials through API responses, logs, traces, benchmark reports, or persisted workflow data.
* Define minimum required GitHub permissions.
* Validate authentication configuration.
* Handle expired, invalid, or insufficient credentials safely.

## 6.3 — Repository and File Access

Implement isolated GitHub operations for:

* Repository identification.
* Branch/ref selection.
* File retrieval.
* Repository metadata.
* Changed-file discovery where required.

Map GitHub-specific responses into application-level models.

Do not allow GitHub SDK/API types to leak into the workflow layer.

## 6.4 — Pull Request Review

Support the core GitHub review flow:

```text
Pull Request
      ↓
Changed files
      ↓
ReviewRequest
      ↓
CodeWorkflow
      ↓
Findings / ReviewResponse
```

* Define how multiple changed files are handled.
* Define file-level workflow boundaries.
* Preserve workflow-run identity.
* Persist the resulting workflow history.
* Ensure unsupported file types are handled safely.

## 6.5 — GitHub Review Comments

Map normalized findings to GitHub review comments where technically possible.

Each comment should preserve:

* Finding ID.
* Severity.
* File path.
* Line information.
* Review message.
* Workflow-run reference where appropriate.

Handle findings that cannot be mapped cleanly to a source line.

## 6.6 — GitHub Integration Testing

* Mock GitHub API interactions.
* Test authentication failures.
* Test repository/file retrieval failures.
* Test malformed GitHub responses.
* Test pull requests with multiple files.
* Test findings-to-comment mapping.
* Ensure tests do not depend on a real GitHub repository.

## 6.7 — Milestone Validation

Verify the complete integration:

```text
GitHub PR
    ↓
GitHub adapter
    ↓
AI workflow
    ↓
Evaluation
    ↓
Findings
    ↓
GitHub review
```

**Outcome:** The platform can process GitHub-based code reviews without coupling the core workflow to GitHub.

---

# Milestone 7 — Containerization, CI/CD and Cloud Deployment

**Goal:** Package and deploy the application as a production service using Docker, GitHub Actions and Google Cloud Run.

## 7.1 — Production Docker Image

* Create a production Dockerfile.
* Use a minimal appropriate Python image.
* Install only required runtime dependencies.
* Run as a non-root user.
* Configure environment-driven settings.
* Support graceful application shutdown.
* Verify image reproducibility where practical.

## 7.2 — Container Validation

Test the container locally for:

* Application startup.
* Health endpoint.
* Readiness endpoint.
* Database connectivity.
* LLM connectivity.
* Graceful shutdown.
* Correct filesystem/workspace behavior.
* Configuration validation.

## 7.3 — Continuous Integration

Create GitHub Actions CI covering:

```text
Pull Request / Push
        ↓
Lint
        ↓
Type Check
        ↓
Unit Tests
        ↓
Integration Tests
        ↓
Benchmark / regression checks
        ↓
Docker Build
```

* Keep CI reproducible.
* Do not expose secrets in logs.
* Fail builds on important quality regressions.

## 7.4 — Database Migration Strategy

Define the production migration process using Alembic.

* Validate migrations in CI.
* Prevent application startup from silently creating schema.
* Define when migrations execute during deployment.
* Verify migration compatibility with Neon PostgreSQL.
* Document rollback considerations.

## 7.5 — Google Cloud Run Deployment

Deploy the API to Google Cloud Run.

Configure:

* Container port.
* Environment variables.
* Secrets.
* CPU/memory.
* Request timeout.
* Concurrency.
* Minimum/maximum instances as appropriate.
* Health/readiness behavior.

## 7.6 — Production Observability

Verify production telemetry:

```text
Cloud Run
   ↓
Application logs
   ↓
OpenTelemetry
   ↓
Workflow span
   ↓
Agent spans
   ↓
LLM calls
```

Ensure workflow IDs and request correlation remain available without exposing sensitive data.

## 7.7 — Deployment Validation

Perform a complete production smoke test:

* API authentication.
* Generation workflow.
* Review/refactor workflow.
* Persistence.
* Feedback.
* Evaluation.
* GitHub integration.
* Error handling.
* Telemetry.
* Graceful shutdown.

**Outcome:** The platform runs as a deployed, containerized production service with automated CI/CD.

---

# Milestone 8 — API and User Experience

**Goal:** Improve usability and provide a clear interface for demonstrating the complete platform without compromising the API-first architecture.

## 8.1 — Workflow Status and History API

Add API capabilities for:

* Workflow status.
* Workflow history.
* Workflow details.
* Agent-step history.
* Findings.
* Evaluation results.
* Generated artifacts.
* Feedback.

Reuse existing persistence structures where practical.

## 8.2 — API Contract Refinement

Review the public API for:

* Consistent request/response schemas.
* Error responses.
* Authentication.
* Validation errors.
* Workflow identifiers.
* Pagination where needed.
* Backward compatibility.

Only introduce new request fields when they represent genuine user-facing capabilities.

## 8.3 — Developer Experience

Improve:

* API documentation.
* OpenAPI descriptions.
* Example requests.
* Example responses.
* Local development instructions.
* Deployment instructions.
* Architecture documentation.

Provide representative examples for:

* Feature generation.
* Code review/refactoring.
* GitHub review.

## 8.4 — Streamlit Dashboard

Implement the dashboard only after the API and backend are stable.

The dashboard should provide:

```text
Submit workflow
      ↓
View workflow status
      ↓
View generated/refactored code
      ↓
View findings
      ↓
View tests
      ↓
View evaluation
      ↓
View workflow history
```

## 8.5 — Observability View

Expose useful, non-sensitive workflow information such as:

* Agent execution sequence.
* Round number.
* Latency.
* Evaluation score.
* Retry count.
* Token usage.
* Final decision.

Do not expose secrets or unnecessary internal infrastructure details.

## 8.6 — UX Validation

Test the complete user journey:

```text
User
 ↓
API / Dashboard
 ↓
Workflow
 ↓
Evaluation
 ↓
Result
```

**Outcome:** The platform has a usable API and optional demonstration UI suitable for recruiters, developers and portfolio presentation.

---

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

---

# Milestone 10 — Advanced Agentic Capabilities

**Goal:** Introduce genuinely agentic planning only when the system has enough capabilities for dynamic planning to provide meaningful value.

The deterministic workflow remains the safety-critical default. LLM-based planning is introduced only for decisions that cannot be represented effectively by the existing fixed workflow.

## 10.1 — Capability Registry

Define an application-controlled registry of available capabilities, such as:

* Code review.
* Security analysis.
* Performance analysis.
* Static analysis.
* Refactoring.
* Test generation.
* Test execution.
* Evaluation.

Each capability must have:

* Stable identifier.
* Input contract.
* Output contract.
* Execution constraints.
* Safety requirements.

The LLM must never invent executable capabilities.

## 10.2 — Dynamic Planning Architecture

Introduce an optional LLM Planner that selects from the registered capability vocabulary.

Architecture:

```text
User Request
      ↓
Deterministic Router
      ↓
LLM Planner
      ↓
Constrained Plan
      ↓
Deterministic Policy Validation
      ↓
Workflow Execution
```

The planner may propose:

* Relevant capabilities.
* Capability ordering.
* Strategy.
* Task-specific priorities.

The planner may not:

* Execute tools.
* Mutate workflow state.
* Bypass mandatory security/evaluation stages.
* Change retry limits.
* Terminate the workflow directly.
* Invent unsupported capabilities.

## 10.3 — Deterministic Plan Validation

Validate every LLM-generated plan against application policy.

Reject or safely fall back when:

* A capability is unsupported.
* Required safety stages are missing.
* Ordering constraints are violated.
* Required evaluation is omitted.
* The plan exceeds configured limits.
* The output is malformed.

Retain the deterministic planner as a safe fallback.

## 10.4 — Planner Failure and Fallback

Define controlled behavior for:

* Timeout.
* Provider failure.
* Invalid structured output.
* Unsupported plan.
* Model unavailability.

Fallback:

```text
LLM Planner unavailable
        ↓
Deterministic Planner
        ↓
Standard workflow
```

Record fallback usage in workflow traces and logs.

## 10.5 — Agent Collaboration

Evaluate whether specialist agents benefit from structured outputs produced by earlier agents.

Introduce explicit inter-agent contracts where useful rather than relying on unrestricted conversational context.

Potential examples:

* Reviewer findings → CodeWriter.
* Security findings → CodeWriter.
* Evaluation findings → Repair strategy.
* Test failures → Repair context.

## 10.6 — Advanced Tool Selection

If justified by the capability registry, allow the planner to select deterministic tools from a constrained registry.

Tool selection must remain:

* Application-defined.
* Schema-validated.
* Permission-controlled.
* Observable.
* Auditable.

## 10.7 — Advanced Planning Evaluation

Extend the benchmark framework to measure:

* Correctness.
* Security.
* Maintainability.
* Execution success.
* Finding resolution.
* Workflow efficiency.
* Retry rate.
* Token usage.
* Latency.
* Plan validity.
* Fallback rate.

Compare dynamic planning against the deterministic baseline.

Do not retain dynamic planning if it does not provide measurable benefit.

## 10.8 — Milestone Validation

* Run the complete test suite.
* Run the benchmark suite.
* Compare deterministic and agentic workflows.
* Verify safety constraints.
* Verify fallback behavior.
* Verify telemetry.
* Verify persistence.
* Verify API compatibility.

**Outcome:** The platform has a controlled agentic planning capability that dynamically composes supported capabilities only when this provides measurable value over deterministic orchestration.

---

# Milestone 11 — Platform Extensibility and Azure

**Goal:** Demonstrate that the architecture can support additional providers and integrations without coupling the core application to a specific cloud or LLM provider.

## 11.1 — Provider Abstraction Review

Review provider-specific dependencies and ensure they remain isolated behind application interfaces.

Separate:

```text
Application / Agents
        ↓
LLM abstraction
        ↓
Provider implementation
```

The workflow must not depend directly on Gemini-specific APIs.

## 11.2 — Azure LLM Provider

Add Azure-hosted LLM support where practical.

* Implement an Azure provider behind the existing LLM abstraction.
* Reuse existing structured-output contracts.
* Reuse agent implementations where possible.
* Keep provider configuration isolated.
* Support provider/model selection through configuration.
* Preserve existing observability and token tracking.

## 11.3 — Provider Comparison

Run selected benchmark cases against supported providers/models.

Compare:

* Correctness.
* Security.
* Maintainability.
* Execution success.
* Finding resolution.
* Latency.
* Token usage.
* Cost where measurable.
* Failure rate.

## 11.4 — Integration Architecture Review

Review the complete system for extensibility across:

* LLM providers.
* GitHub.
* Databases.
* Telemetry backends.
* Workflow capabilities.
* UI clients.

Remove accidental coupling discovered during implementation.

## 11.5 — Documentation and Architecture Review

Update:

* README.
* Architecture documentation.
* Architecture decisions.
* API documentation.
* Deployment documentation.
* Configuration documentation.
* Benchmark documentation.

Document important trade-offs and rejected alternatives.

## 11.6 — Final Production Validation

Run the complete platform validation:

```text
API
 ↓
Workflow
 ↓
Agents
 ↓
Tools
 ↓
Evaluation
 ↓
Persistence
 ↓
Observability
 ↓
GitHub
 ↓
Cloud deployment
```

Verify:

* Automated tests.
* Benchmarks.
* CI/CD.
* Database migrations.
* Security controls.
* Observability.
* Deployment.
* Provider abstraction.
* GitHub integration.
* API behavior.

**Outcome:** The project demonstrates a production-oriented, extensible AI engineering platform with multi-agent orchestration, deterministic controls, evaluation, observability, persistence, GitHub integration, cloud deployment, and optional multi-provider LLM support.
