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