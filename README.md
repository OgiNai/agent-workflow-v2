# AI Code Review & Refactoring Platform

> A production-oriented multi-agent AI workflow for automated code generation, code review, security auditing, refactoring, testing, evaluation, and continuous improvement.

> **Status:** Active development (Portfolio Project)

---

## Overview

This project is designed to demonstrate practical AI Engineering skills rather than simply calling an LLM API.

It implements a production-style multi-agent workflow where specialized AI agents collaborate to review, improve, validate, and evaluate software code.

The focus is on building scalable orchestration, observability, evaluation, and engineering practices similar to those used in real-world AI systems.

---

## Goals

- Build a production-quality AI workflow
- Use modern AI engineering practices
- Demonstrate system design and software architecture
- Showcase multi-agent orchestration
- Follow clean architecture and engineering best practices
- Create a portfolio project suitable for AI Engineer interviews

---

## Current Workflow

```text
                User Request
                     │
                     ▼
              Input Router
                     │
                     ▼
                 Planner
                     │
      ┌──────────────┴──────────────┐
      │                             │
      │ Feature Request             │ Code Review
      │                             │
      ▼                             │
CodeWriter (Generate)               │
      └──────────────┬──────────────┘
                     ▼
              Reviewer Agent
                     ▼
          Security Auditor
                     ▼
     CodeWriter (Refactor/Repair)
                     ▼
           Test Generator
                     ▼
             Test Runner
                     ▼
             Evaluator
                     │
          PASS / FAIL / RETRY
                     │
        RETRY returns to Reviewer
```

---

## Current Features

- Multi-agent workflow orchestration
- Planner-driven execution
- AI code generation
- AI code review
- Security auditing
- Automated code refactoring
- AI-generated unit tests
- Automatic test execution
- LLM-based evaluation
- Rule-based evaluation
- Execution-based evaluation
- Structured workflow tracing
- Artifact generation
- Configurable retry loop
- Debug retry mode
- FastAPI REST API
- Docker-ready project structure

---

## Planned Features

- PostgreSQL persistence (Neon)
- User feedback collection
- Full observability
- Workflow analytics
- Human approval checkpoints
- GitHub integration
- Cloud Run deployment
- Azure deployment
- Streamlit dashboard
- LLM-powered Planner
- Agent memory
- Parallel agent execution
- Automatic prompt evaluation
- Benchmark datasets
- CI/CD with GitHub Actions

---

## Architecture

The project follows a modular architecture with clear separation of responsibilities.

### AI Agents

- **Planner**
  - Determines workflow execution strategy.

- **Reviewer**
  - Reviews code quality and maintainability.

- **Security Auditor**
  - Detects security vulnerabilities.

- **CodeWriter**
  - Generates new code or refactors existing code.

- **Test Generator**
  - Produces unit tests for generated/refactored code.

- **Evaluator**
  - Combines execution results, review findings and LLM evaluation into a final decision.

### Tools

- Safe file reader
- Safe file writer
- Pytest execution
- Artifact manager

---

## Tech Stack

### AI

- Google Gemini
- Structured Outputs
- Pydantic

### Backend

- Python
- FastAPI
- Uvicorn

### Data

- PostgreSQL (Neon) *(planned)*

### Testing

- Pytest
- pytest-json-report

### DevOps

- Docker
- GitHub Actions *(planned)*
- Google Cloud Run *(planned)*
- Azure *(planned)*

---

## Engineering Practices

This project intentionally emphasizes software engineering over prompt engineering.

Implemented practices include:

- Clean Architecture
- Dependency Injection
- Immutable configuration
- Strong typing
- Structured outputs
- Modular agent design
- Configuration management
- Observability
- Evaluation pipeline
- Production-style orchestration
- Separation of concerns

---

## Project Roadmap

| Milestone | Status |
|-----------|--------|
| Workflow Backbone | ✅ Completed |
| PostgreSQL Persistence | 🚧 Planned |
| Observability | 🚧 Planned |
| Human Feedback | 🚧 Planned |
| LLM Planner | 🚧 Planned |
| GitHub Integration | 🚧 Planned |
| Cloud Deployment | 🚧 Planned |
| Dashboard | 🚧 Planned |

---

## Why this project?

This project focuses on the engineering challenges of building reliable AI systems:

- orchestrating multiple specialized agents,
- validating AI-generated outputs,
- tracking workflow execution,
- collecting evaluation metrics,
- supporting iterative improvement,
- preparing for production deployment.

The objective is to demonstrate the skills expected from an AI Engineer working on real-world LLM applications rather than isolated prompt-based examples.