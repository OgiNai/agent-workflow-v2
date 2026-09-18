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