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