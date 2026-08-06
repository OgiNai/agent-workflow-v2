
# AI Collaboration Guide

This document defines the collaboration workflow, engineering principles, and coding standards for AI assistants contributing to this repository.

Its purpose is to ensure consistent architectural decisions, minimize unnecessary discussion, and keep all implementations production-oriented.

---

# Project Goals

The primary goal of this project is to demonstrate **production-quality AI engineering**, not merely prompt engineering.

The project should showcase:

* Scalable architecture
* Clean separation of concerns
* Production-ready code
* Extensible multi-agent workflow
* Deterministic components where appropriate
* Real evaluation pipeline
* Observability
* PostgreSQL persistence
* Docker deployment
* GitHub Actions
* Google Cloud Run deployment
* Azure deployment (later milestones)

Whenever multiple solutions exist, prefer the one that best reflects real-world production practices over the simplest implementation.

Free-tier services should be preferred whenever practical.

---

# Architectural Principles

The existing architecture should be preserved unless there is a compelling technical reason to change it.

Core principles:

* Single responsibility for every module.
* Clear separation between domain logic and infrastructure.
* Dependency injection over global state.
* Immutable configuration objects.
* Explicit data flow.
* Strong typing throughout the project.
* Structured agent outputs.
* Deterministic behavior where possible.
* Extensibility over premature optimization.

Avoid introducing unnecessary abstractions or design patterns before they provide clear value.

---

# Approved Architectural Decisions

These decisions are considered settled and should not be revisited unless explicitly requested.

## Workflow

Input Router

↓

Planner

↓

(if generation)

CodeWriter (generate)

↓

Reviewer

↓

Security Auditor

↓

CodeWriter (refactor)

↓

Test Generator

↓

Test Runner

↓

Evaluator

↓

Pass / Retry

↓

Reviewer (retry loop)

---

## Planner

* Planner-first architecture.
* Current planner remains deterministic.
* LLM-powered planner is scheduled for Milestone 5.
* LLM planner must preserve the existing PlannerOutput schema.
* Deterministic planner remains available behind a feature flag.

---

## Agents

* Reviewer and Security Auditor remain separate agents.
* CodeWriter supports generate/refactor modes.
* Test Runner is a tool, not an agent.
* Evaluator remains pure.
* Retry logic belongs exclusively to the workflow.

---

## Configuration

* WorkflowSettings loads environment configuration.
* WorkflowConfig is immutable.
* CodeWorkflow never reads settings directly.
* Debug behavior is implemented by overriding workflow decisions.
* Debug logic must never modify evaluator output.

---

## Persistence

Persistence is isolated behind repositories.

Workflow

↓

Repositories

↓

SQLAlchemy

↓

PostgreSQL

The workflow must remain persistence-agnostic.

---

# Implementation Workflow

Work on exactly one milestone (or implementation step) at a time.

Read the project file structure and PROJECT_PLAN.md before making suggestions.

Maintain the same coding standards and architecture already established in the project.

For each implementation step:

1. Determine the relevant repository files.
2. Fetch and inspect those files.
3. Identify existing functionality.
4. Avoid duplicating work.
5. Ask for explicit approval for any important design decisions before implementation.
6. Explain only architectural decisions requiring approval.
7. Generate the complete contents of every new or modified file directly in the chat.
8. Clearly separate new files from modified files.
9. Explain why each file changed.
10. The user is responsible for copying the generated files into the local repository, testing them, and committing the changes.
11. Wait until the changes have been integrated and tested before proceeding.


---

# Code Generation Rules

Always return complete files.

Never return partial patches unless explicitly requested.

When existing files change:

* Return the entire updated file.
* Preserve formatting and coding style.
* Preserve comments unless they become incorrect.
* Do not rewrite unrelated sections.

When creating new files:

* Follow the existing project structure.
* Match naming conventions already present.
* Keep responsibilities focused.

Generated code should:

* Follow modern Python best practices.
* Use explicit typing.
* Prefer composition over inheritance.
* Avoid unnecessary abstractions.
* Be production-ready.
* Be easily testable.

---

# Repository Access

**Repository**

https://github.com/OgiNai/agent-workflow-v2

**Default branch**

`main`

## Repository Structure

```text
apps/
├── agents/
├── api/
├── core/
├── database/
├── evals/
├── llm/
├── observability/
├── repositories/
├── schemas/
├── tools/
└── workflows/

tests/

workspace/

README.md
PROJECT_PLAN.md
ARCHITECTURE_DECISIONS.md
AI_COLLABORATION.md
pyproject.toml
```

The GitHub repository is used **only for inspection**.

Unless the user explicitly requests otherwise:

* Never attempt to modify the GitHub repository.
* Never attempt to create commits, branches, pull requests, or files through the GitHub integration.
* Never use GitHub write operations.

The GitHub repository is the authoritative source of the implementation.

The AI assistant has standing permission to perform read-only repository inspection:

* Determine which repository files are relevant to the current task.
* Fetch those files without requesting additional permission using the GitHub read interface.
* Inspect their contents before proposing or generating code.
* Use the existing implementation as the basis for all changes.

Repository inspection is considered an implicit part of every implementation task and does not require separate user approval.

Only request user input when:

* The required files cannot be accessed.
* Multiple architectural approaches are equally valid and one must be chosen.
* The requested change would alter previously approved architecture.
* The repository contents conflict with the documented project decisions.

---

# Communication Style

Assume previously approved architectural decisions remain in effect.

Do not:

* Repeat previously established context.
* Re-explain approved design decisions.
* Summarize information already discussed.
* Add conversational filler.

Communicate only:

* New findings.
* Design decisions requiring approval.
* Important trade-offs.
* Implementation details.
* Blocking issues.

When implementation has already been approved, proceed directly to the work.

---

# Documentation Priority

When multiple documentation sources exist, use them in the following order:

1. AI_COLLABORATION.md
2. PROJECT_PLAN.md
3. ARCHITECTURE_DECISIONS.md
4. README.md

The GitHub repository remains the implementation source of truth.

---

# General Principle

When faced with multiple valid solutions, prefer the one that:

* Improves maintainability.
* Preserves architectural consistency.
* Scales well to future milestones.
* Demonstrates production-quality AI engineering.
* Produces a repository that serves as a strong portfolio project for AI Engineer positions.
