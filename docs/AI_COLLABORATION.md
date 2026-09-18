
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
* If implemented LLM planner must preserve the existing PlannerOutput schema.
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

Workflow (business logic)
        ↓
Unit of Work (transaction boundary)
        ↓
Repositories (data access)
        ↓
SQLAlchemy (ORM)
        ↓
PostgreSQL

The workflow must remain persistence-agnostic.

---

# Implementation Workflow

Work on exactly one milestone (or implementation step) at a time.

For each implementation step:

1. Read the content for the current step in PROJECT_PLAN.md.

2. Determine the repository areas potentially affected by the step, including:
   - application code directly involved in the feature;
   - schemas, models, interfaces, and shared types used by that code;
   - repositories, persistence, transactions, and database models involved in the data flow;
   - API routes, dependencies, and application wiring involved at the boundary;
   - existing tests covering the affected behavior;
   - configuration, migrations, utilities, or infrastructure that may constrain the implementation;
   - documentation containing architectural decisions or established conventions relevant to the step.

3. Fetch and inspect all relevant existing files before planning or proposing implementation changes.
   - Do not infer the structure, fields, method names, constructor signatures, interfaces, or behavior of a repository component without inspecting its source.
   - Trace important dependencies across module boundaries rather than inspecting only the file where a change appears to originate.
   - When adding or modifying tests, inspect the implementation under test, its dependencies, and existing tests/helpers that establish project conventions.
   - Prefer repository source over assumptions, memory, or generic framework patterns when determining how the project currently works.

4. Identify and document existing functionality and integration points.
   - Determine what already exists and should be reused.
   - Identify relevant abstractions, dependency-injection seams, persistence boundaries, error-handling behavior, and test fixtures/helpers.
   - Identify interactions that could be affected even if the corresponding files will not ultimately be modified.

5. Compose a detailed action plan based on:
   - the existing repository implementation;
   - the inspected dependency/integration points;
   - existing tests and test conventions;
   - the current step in PROJECT_PLAN.md;
   - relevant decisions in ARCHITECTURE_DECISIONS.md.
   
   The plan must be based on inspected repository code, not inferred or assumed interfaces.

6. Present that plan along with a brief explanation of the goals of that step.

7. Explain architectural decisions requiring approval.

8. Ask for explicit approval for any important design decisions before implementation.

9. Generate the complete contents of every new or modified file directly in the chat.
   - Generated code must match the interfaces, schemas, constructors, dependencies, and conventions verified during repository inspection.
   - Do not invent repository APIs or fields when the existing implementation can be inspected.

10. Clearly separate new files from modified files.

11. The user is responsible for copying the generated files into the local repository, testing them, and committing the changes.

12. Wait until the changes have been integrated and tested before proceeding.


---

# Code Generation Rules

Maintain the same coding standards and architecture already established in the project.

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

alembic/

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

benchmarks/

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

Repository inspection is considered an implicit part of every implementation task and does not require separate user approval or notification. 

Only request user input when:

* The required files cannot be accessed.
* Multiple architectural approaches are equally valid and one must be chosen.
* The requested change would alter previously approved architecture.
* The repository contents conflict with the documented project decisions.

---

# Communication Style

Assume previously approved architectural decisions remain in effect. Future chats should begin from the current milestone without revisiting previous architectural decisions unless a deliberate architecture change is proposed.

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
