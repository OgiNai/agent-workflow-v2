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

# Milestone Roadmap

## Milestone 1

Core workflow foundation.

Deliverable

Working end-to-end workflow.

Includes

- routing
- planner
- generation
- review
- refactor
- testing
- evaluation

---

## Milestone 2

Milestone 2 implementation plan


# Step 2.1 — Persistence foundation

New files

apps/database/
├── __init__.py
├── base.py
├── session.py
└── models.py

Changes

pyproject.toml
apps/core/settings.py

Deliverables:

SQLAlchemy 2.x (async)
asyncpg
AsyncEngine
AsyncSession
DeclarativeBase
configuration from WorkflowSettings
ORM models
database initialization

No workflow changes yet.

# Step 2.2 — Repository layer

New

apps/repositories/
├── __init__.py
├── workflow_repository.py
├── agent_step_repository.py
├── artifact_repository.py
└── feedback_repository.py

Deliverables:

repository interfaces
SQLAlchemy implementation
CRUD operations

Still no workflow modifications.

# Step 2.3 — Integrate persistence

Modify:

code_workflow.py
artifact_manager.py

Deliverables:

create WorkflowRun
store AgentSteps
store Artifacts
update workflow status
update summary
save evaluation scores

# Step 2.4 — Feedback API

Modify:

apps/api/feedback.py

Deliverables:

persist feedback
validation
repository integration

# Step 2.5 — Database bootstrap

The purpose of this step is to make the application responsible for initializing and validating its database connection during startup, while keeping the existing Alembic-based schema management.

Modify:
- main.py
- apps/database/session.py
- apps/api/health.py

Deliverables:
- Initialize/validate the async database engine during application startup.
- Verify Neon connectivity through the readiness endpoint.
- Gracefully close the database engine during shutdown.
- Keep database schema creation and evolution exclusively under Alembic.

---

## Milestone 3

Observability.

                    CodeWorkflow
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
      Business       Persistence     Observability
       result            │                │
          │              │                │
   ReviewResponse     PostgreSQL      OpenTelemetry
                         │                │
                  WorkflowRun         Traces
                  AgentStep           Metrics
                  Artifact             Logs
                         │
                         │
                    durable history

Implement

# Step 3.1 - Production logging strategy

- structured logs
- correlation IDs
- operational/error events
- don't duplicate normal workflow events

# Step 3.2 - OpenTelemetry foundation

- OTLP
- configurable exporter
- optional collector/backend
- FastAPI lifecycle integration

# Step 3.3 - Tracing

- workflow span
- child spans per meaningful workflow operation
- attributes for workflow ID, round, agent, model, etc.
- exceptions/status recorded on spans

# Step 3.4 - LLM usage tracking

- extract Gemini usage metadata
- propagate it from Gemini client → agent → _trace_agent
- persist to existing AgentStep fields
- expose relevant usage in telemetry

# Step 3.5 - Prompt versioning

- retain historical prompts
- explicit current version
- persist version with each LLM execution
- make historical evaluation reproducible

---

## Milestone 4

Evaluation.

The evaluation system provides deterministic, structured and reproducible
measurement of workflow quality.

### Step 4.1 — Normalized evaluation findings

- Introduce normalized `Finding` schema.
- Reviewer and Security Auditor return individual findings.
- Assign stable application-generated finding IDs.
- Evaluator determines whether each finding is `resolved` or `unresolved`.
- Preserve original finding metadata during evaluation.
- Persist findings through existing `AgentStep.output_json`.
- Do not create a separate findings database table.

### Step 4.2 — Structured pytest evaluation

Improve the deterministic test runner by consuming structured pytest output.

- Replace stdout parsing with `pytest-json-report`.
- Make the JSON report the canonical test execution input.
- Populate `TestRunResult` from the JSON report.
- Capture:
  - total tests
  - passed
  - failed
  - skipped
  - xfailed
  - xpassed
  - individual test results
  - failure messages
  - tracebacks
  - execution duration
- Remove dependence on regex parsing of pytest console output.
- Ensure the Evaluator consumes `TestRunResult`.

### Step 4.3 — Deterministic evaluation scoring and decision policy

Separate qualitative LLM evaluation from deterministic workflow decisions.

LLM responsibilities:

- evaluate correctness
- evaluate security
- evaluate maintainability
- determine finding resolution
- provide explanations

Deterministic responsibilities:

- rule score
- execution score
- finding severity penalties
- final score calculation
- final evaluation decision

Define explicit thresholds for:

- pass
- pass_with_warnings
- retry

High and critical unresolved findings must be able to force retry.

Failed execution must be able to force retry.

The Evaluator must never know or enforce retry limits.

Add unit tests covering every decision boundary.

### Step 4.4 — Evaluation benchmark framework

Create a reproducible benchmark corpus.

Each benchmark case should define:

- user instruction
- source code
- expected findings
- expected behavior
- security expectations
- test expectations

Execute the complete workflow against benchmark cases and collect structured
evaluation results.

### Step 4.5 — Evaluation reports

Generate structured benchmark reports containing:

- benchmark run metadata
- workflow/model configuration
- prompt versions
- per-case evaluation results
- finding resolution
- test results
- final scores
- final decisions
- aggregate metrics

### Step 4.6 — Metrics storage

Persist benchmark-level evaluation metrics when existing workflow persistence
is insufficient for historical querying.

Prefer existing `WorkflowRun` and `AgentStep` JSON data where practical.

Introduce dedicated metrics persistence only when a concrete querying or
reporting requirement justifies it.

### Step 4.7 — Evaluation comparison tooling

Provide comparison of benchmark runs across:

- final score
- rule score
- execution score
- correctness
- security
- maintainability
- finding resolution rate
- retry rate
- latency
- LLM usage

---

## Milestone 5 — Agentic Planning

**Goal:** Replace the current deterministic Planner with an LLM-based planning agent while preserving the existing workflow contracts, validation boundaries, retry behavior, observability, and evaluation architecture.

### 5.1 LLM Planner Design

* Define the Planner's responsibilities and boundaries.
* Define the structured planning output consumed by `CodeWorkflow`.
* Decide which workflow decisions should be delegated to the LLM and which remain deterministic application policy.
* Define the Planner prompt and version it alongside the existing agent prompts.
* Define the model configuration used by the Planner.
* Ensure the Planner cannot directly execute tools or mutate workflow state.

### 5.2 Structured Planner Output

* Introduce Pydantic schemas for Planner input/output.
* Represent the selected workflow/task strategy explicitly.
* Validate all LLM-generated Planner output before it reaches the workflow.
* Handle malformed, incomplete, or unexpected LLM responses safely.
* Ensure unsupported planning decisions fall back to deterministic application behavior where appropriate.

### 5.3 Planner Agent Implementation

* Implement the Planner as an LLM-backed agent using the existing LLM abstraction.
* Integrate token usage and prompt-version tracking with the existing observability infrastructure.
* Preserve retry/error handling conventions used by other LLM agents.
* Keep provider/model-specific implementation details outside the workflow orchestration layer.

### 5.4 Workflow Integration

* Replace the current deterministic planning decision with the LLM Planner.
* Preserve the existing workflow sequence and retry semantics.
* Ensure Planner output determines strategy rather than bypassing safety, security, testing, or evaluation stages.
* Verify both major paths:

  * review/refactor
  * feature/code generation
* Ensure invalid Planner output cannot cause uncontrolled workflow behavior.

### 5.5 Planner Evaluation

* Extend benchmark cases where necessary to test planning decisions.
* Add expectations for Planner behavior where deterministic validation is possible.
* Measure Planner impact on:

  * correctness
  * security
  * maintainability
  * execution success
  * token usage
  * execution duration
* Verify that introducing non-deterministic planning does not degrade existing benchmark performance.
* Document known sources of LLM variance.

### 5.6 Planner Failure and Fallback Strategy

* Define behavior for LLM timeout, provider errors, malformed output, and unavailable model.
* Ensure a Planner failure produces a controlled workflow outcome.
* Define when deterministic fallback is appropriate versus when the workflow should fail.
* Add automated tests for failure and fallback scenarios.

### 5.7 Milestone Validation

* Run the complete test suite.
* Run the benchmark suite using the new Planner.
* Compare results against the pre-LLM Planner baseline.
* Verify persisted workflow traces and token usage.
* Verify OpenTelemetry traces remain correctly associated with Planner execution.
* Confirm that existing API behavior remains compatible unless intentionally changed.

**Outcome:** The workflow has a production-oriented LLM Planner that makes structured planning decisions while deterministic application logic continues to enforce workflow safety, validation, retry, and evaluation policies.

---

## Milestone 6 — GitHub Integration

**Goal:** Integrate the workflow with GitHub repositories while keeping GitHub-specific concerns isolated from the core workflow and domain logic.

### 6.1 GitHub Integration Architecture

* Define GitHub as an external adapter around the existing workflow.
* Keep `CodeWorkflow` independent of GitHub APIs.
* Define the boundary between:

  * GitHub repository data
  * application/domain models
  * `ReviewRequest`
  * `ReviewResponse`
* Decide which GitHub operations belong in the initial MVP and which are deferred.
* Define security and permission boundaries before implementation.

### 6.2 GitHub Authentication

* Select the authentication mechanism appropriate for the MVP.
* Store GitHub credentials/tokens through the existing application configuration and secret-management approach.
* Never expose credentials through API responses, logs, traces, benchmark reports, or persisted workflow data.
* Define the minimum GitHub permissions required by the application.
* Add configuration validation and failure handling for missing/invalid credentials.

### 6.3 Repository and File Access

* Implement a GitHub client/adapter for repository access.
* Support retrieving source files from a repository.
* Validate repository, branch/ref, and file-path inputs.
* Apply the existing project file/path security policies where applicable.
* Handle GitHub API errors, missing repositories/files, unsupported files, and rate limits.
* Avoid coupling GitHub response models directly to internal workflow schemas.

### 6.4 GitHub → Workflow Integration

* Convert GitHub source content into the existing `ReviewRequest`.
* Reuse the existing review/refactor workflow rather than creating a separate GitHub workflow.
* Preserve the existing Planner → Reviewer → Security Auditor → CodeWriter → Test Generator → Test Runner → Evaluator flow.
* Record sufficient source/repository metadata to identify the origin of a workflow run without storing unnecessary external data.
* Ensure GitHub-specific failures are distinguishable from workflow/LLM failures.

### 6.5 Review Result Presentation

* Define how `ReviewResponse` is mapped back to GitHub concepts.
* Support an initial read-only review result flow before modifying repositories.
* Determine how findings, severity, descriptions, and suggested changes should be represented.
* Ensure generated output remains understandable in a GitHub developer workflow.
* Preserve the existing API response independently of the GitHub presentation layer.

### 6.6 Pull Request Integration

* Extend the adapter to support pull-request-based reviews.
* Retrieve relevant changed files from a pull request.
* Run the existing workflow against the selected changes.
* Determine how findings should be associated with changed files/lines where technically feasible.
* Support publishing review results as GitHub PR comments or review feedback.
* Define safeguards preventing accidental repository modifications or unintended PR actions.

### 6.7 GitHub Write Operations

* If code changes are enabled, explicitly separate:

  * generated/refactored code
  * proposed repository changes
  * actual GitHub write operations
* Define whether the MVP creates commits, branches, or pull requests.
* Require explicit application-level authorization for write operations.
* Ensure failed write operations cannot leave the workflow in an inconsistent state.
* Record external operation results in workflow observability.

### 6.8 GitHub Error Handling and Resilience

* Handle authentication failures.
* Handle repository/file/PR not found errors.
* Handle permission errors.
* Handle GitHub API rate limits.
* Handle transient GitHub API failures.
* Define retry behavior for external API calls separately from LLM/workflow retries.
* Ensure external failures are observable and diagnosable.

### 6.9 GitHub Integration Testing

* Add unit tests for GitHub adapter behavior.
* Test conversion between GitHub data and internal workflow models.
* Test authentication and error handling.
* Mock GitHub API interactions rather than depending on live GitHub calls for normal CI tests.
* Add integration tests against GitHub only if appropriate credentials and environment configuration are available.
* Verify that the core workflow remains testable without GitHub.

### 6.10 Milestone Validation

* Execute a complete review against a real GitHub repository/file.
* Verify the resulting `ReviewResponse`.
* Verify workflow persistence and observability.
* Verify token usage and timing remain recorded.
* Verify GitHub operations are represented clearly in logs/traces without exposing credentials.
* Run the complete automated test suite.
* Document the supported GitHub workflow and known limitations.

**Outcome:** GitHub becomes a real external integration layer for the platform without coupling GitHub-specific logic to the core AI workflow, allowing the same workflow to operate through the existing API and through GitHub.


---

## Milestone 7

Production API.

Implement

- authentication
- rate limiting
- versioning
- background jobs
- robust error handling

---

## Milestone 8

Deployment.

Implement

- Docker
- GitHub Actions
- Cloud Run
- monitoring
- Azure deployment

---

## Milestone 9 — Evaluation & Benchmarking Maturity

Goal:
Strengthen the evaluation framework so benchmark results can distinguish
real system improvements from stochastic LLM variation and provide
statistically meaningful performance comparisons.

### 9.1 Repeated Benchmark Runs
- Support executing the same benchmark configuration multiple times.
- Allow configurable number of repetitions.
- Preserve each individual benchmark run/report.
- Aggregate repeated runs into a single experiment result.

### 9.2 Statistical Benchmark Metrics
- Calculate mean, minimum, maximum, and standard deviation for key metrics.
- Track score distributions across repeated runs.
- Aggregate token usage and execution duration across runs.
- Report per-category statistics where useful.

### 9.3 Baseline vs Candidate Experiments
- Introduce the concept of a benchmark experiment containing:
  - baseline configuration
  - candidate configuration
  - repeated runs for each configuration
- Compare aggregate distributions rather than individual runs.
- Report absolute and relative improvements.

### 9.4 Statistical Significance
- Evaluate whether observed differences are likely to represent
  meaningful improvements rather than LLM stochastic variation.
- Add appropriate statistical tests where justified.
- Avoid over-interpreting small benchmark differences.

### 9.5 Benchmark Reproducibility
- Record all configuration required to reproduce an experiment:
  - model
  - temperature
  - prompt versions
  - benchmark case version
  - workflow configuration
  - repetition count
- Ensure benchmark reports remain self-contained and versioned.

### 9.6 Evaluation Visualization
- Add lightweight visualization of benchmark results where useful.
- Support comparison of score distributions, token usage, and duration.
- Keep visualization separate from the core evaluation engine.

### 9.7 Evaluation Regression Detection
- Define thresholds for detecting meaningful regressions.
- Support automated benchmark checks in CI/CD for selected benchmark suites.
- Fail or warn when candidate performance falls below configured thresholds.

---

## Milestone 10

Portfolio Polish.

Produce

- architecture diagrams
- documentation
- API docs
- Streamlit dashboard
- benchmark results
- recruiter-friendly README

---

# Current Status

Architecture decisions are considered locked.

The following have already been implemented:

- Unified workflow
- Planner-first architecture
- Async Gemini client
- Lifespan support
- Unified request model
- Simplified router
- Shared path helpers
- Async pytest runner
- Dependency Injection
- ToolResult schema relocation
- Evaluator redesign
- Retry redesign
- Source type redesign
- Task type redesign

Future chats should begin from the current milestone without revisiting previous architectural decisions unless a deliberate architecture change is proposed.