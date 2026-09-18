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