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

Persistence.

Implement

- SQLAlchemy
- Neon
- repositories
- workflow storage
- feedback storage

---

## Milestone 3

Observability.

Implement

- structured logging
- OpenTelemetry
- tracing
- token usage
- latency
- prompt version tracking

---

## Milestone 4

Evaluation.

Complete

- benchmark framework
- evaluation reports
- metrics storage
- comparison tooling

---

## Milestone 5

GitHub Integration.

Implement

- repository cloning
- PR review
- branch analysis
- commit review

---

## Milestone 6

Production API.

Implement

- authentication
- rate limiting
- versioning
- background jobs
- robust error handling

---

## Milestone 7

Deployment.

Implement

- Docker
- GitHub Actions
- Cloud Run
- monitoring
- Azure deployment

---

## Milestone 8

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