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