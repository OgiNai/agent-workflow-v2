# Milestone 10 — Advanced Agentic Capabilities

**Goal:** Introduce genuinely agentic planning only when the system has enough capabilities for dynamic planning to provide meaningful value.

The deterministic workflow remains the safety-critical default. LLM-based planning is introduced only for decisions that cannot be represented effectively by the existing fixed workflow.

## 10.1 — Capability Registry

Define an application-controlled registry of available capabilities, such as:

* Code review.
* Security analysis.
* Performance analysis.
* Static analysis.
* Refactoring.
* Test generation.
* Test execution.
* Evaluation.

Each capability must have:

* Stable identifier.
* Input contract.
* Output contract.
* Execution constraints.
* Safety requirements.

The LLM must never invent executable capabilities.

## 10.2 — Dynamic Planning Architecture

Introduce an optional LLM Planner that selects from the registered capability vocabulary.

Architecture:

```text
User Request
      ↓
Deterministic Router
      ↓
LLM Planner
      ↓
Constrained Plan
      ↓
Deterministic Policy Validation
      ↓
Workflow Execution
```

The planner may propose:

* Relevant capabilities.
* Capability ordering.
* Strategy.
* Task-specific priorities.

The planner may not:

* Execute tools.
* Mutate workflow state.
* Bypass mandatory security/evaluation stages.
* Change retry limits.
* Terminate the workflow directly.
* Invent unsupported capabilities.

## 10.3 — Deterministic Plan Validation

Validate every LLM-generated plan against application policy.

Reject or safely fall back when:

* A capability is unsupported.
* Required safety stages are missing.
* Ordering constraints are violated.
* Required evaluation is omitted.
* The plan exceeds configured limits.
* The output is malformed.

Retain the deterministic planner as a safe fallback.

## 10.4 — Planner Failure and Fallback

Define controlled behavior for:

* Timeout.
* Provider failure.
* Invalid structured output.
* Unsupported plan.
* Model unavailability.

Fallback:

```text
LLM Planner unavailable
        ↓
Deterministic Planner
        ↓
Standard workflow
```

Record fallback usage in workflow traces and logs.

## 10.5 — Agent Collaboration

Evaluate whether specialist agents benefit from structured outputs produced by earlier agents.

Introduce explicit inter-agent contracts where useful rather than relying on unrestricted conversational context.

Potential examples:

* Reviewer findings → CodeWriter.
* Security findings → CodeWriter.
* Evaluation findings → Repair strategy.
* Test failures → Repair context.

## 10.6 — Advanced Tool Selection

If justified by the capability registry, allow the planner to select deterministic tools from a constrained registry.

Tool selection must remain:

* Application-defined.
* Schema-validated.
* Permission-controlled.
* Observable.
* Auditable.

## 10.7 — Advanced Planning Evaluation

Extend the benchmark framework to measure:

* Correctness.
* Security.
* Maintainability.
* Execution success.
* Finding resolution.
* Workflow efficiency.
* Retry rate.
* Token usage.
* Latency.
* Plan validity.
* Fallback rate.

Compare dynamic planning against the deterministic baseline.

Do not retain dynamic planning if it does not provide measurable benefit.

## 10.8 — Milestone Validation

* Run the complete test suite.
* Run the benchmark suite.
* Compare deterministic and agentic workflows.
* Verify safety constraints.
* Verify fallback behavior.
* Verify telemetry.
* Verify persistence.
* Verify API compatibility.

**Outcome:** The platform has a controlled agentic planning capability that dynamically composes supported capabilities only when this provides measurable value over deterministic orchestration.