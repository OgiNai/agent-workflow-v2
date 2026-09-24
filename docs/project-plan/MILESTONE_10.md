# Milestone 10 — PR-Level Agentic Planning

**Goal:** Introduce an LLM-based PR Planner that reasons over an entire GitHub pull request, produces a structured and coordinated implementation plan, and orchestrates dependency-aware execution across the existing per-file workflows.

Milestone 10 evolves the deterministic per-file workflow introduced in Milestone 6 into a coordinated PR-level agentic system.

The existing `CodeWorkflow` remains the deterministic execution mechanism. The LLM is responsible for higher-level software-engineering reasoning that is difficult to represent effectively with fixed rules, while application-controlled logic remains responsible for execution, safety, persistence, ordering, retries, and policy enforcement.

The PR Planner must never directly execute tools, mutate workflow state, bypass mandatory workflow stages, or independently control execution limits.

---

## 10.1 — PR-Level Planning Architecture

Introduce a PR-level planning layer above the existing file-level workflows.

The planner receives the complete PR context and determines:

* Which changed files actually require changes.
* What needs to change in each applicable file.
* How changes in different files relate to one another.
* Dependencies between file-level changes.
* The appropriate implementation strategy.
* Information that must be preserved between file workflows.

The planner produces a structured `PRPlan`.

The PR Planner operates once initially for a PR. It may be invoked again later when actionable cross-file feedback indicates that the existing plan needs to be revised.

Target architecture:

```text
                         GitHub PR
                            │
                            ▼
                       PRPlanner
                            │
                            ▼
                         PRPlan
                            │
                            ▼
                    PRExecutionState
                            │
                 dependency-aware order
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
      Workflow A         Workflow B        Workflow C
          │                 │                 │
          ▼                 ▼                 ▼
      Evaluator A        Evaluator B       Evaluator C
          │                 │                 │
          └─────────────────┼─────────────────┘
                            ▼
                    PR-level feedback
                            │
                 ┌──────────┴──────────┐
                 │                     │
              complete             actionable
                 │                 cross-file
                 ▼                     │
               finish                 ▼
                                  PRPlanner
                                      │
                                      ▼
                                revised PRPlan
```

The architecture must preserve the existing GitHub integration boundary:

```text
GitHub API
    ↓
GitHub Adapter
    ↓
Application models
    ↓
PRPlanner / CodeWorkflow
```

GitHub-specific API types, credentials, and request/response representations must not leak into the planner or workflow layers.

---

## 10.2 — PR Context

Use the application-level `PRContext` introduced by the GitHub integration as the common context available to PR-level planning and file-level workflows.

`PRContext` represents the complete relevant context of the pull request rather than the context of a single changed file.

It should contain, at minimum:

* Pull request number.
* Pull request title.
* Pull request description/body.
* Base branch/ref.
* Head branch/ref.
* Base commit SHA.
* Head commit SHA.
* All supported changed-file metadata.
* Diff/patch for each changed file.

Changed-file information should include the information necessary to reason about relationships between files, such as:

* Path.
* Status.
* Previous path when applicable.
* Additions.
* Deletions.
* Total changes.
* Diff/patch.

The complete source contents of supported changed files must also be available to the PR Planner so that it can reason about the PR as a whole rather than relying exclusively on diffs.

The planner therefore receives:

```text
PR metadata
+
all changed-file metadata
+
all changed-file diffs
+
complete contents of supported changed files
```

The existing per-file workflow continues to receive:

```text
ReviewRequest
├── code
│   └── complete contents of target file
│
└── review_context
    └── PRContext
        └── complete PR-level context
```

The complete target file remains the `code` input because it is the primary source being processed by that workflow.

`PRContext` provides the surrounding PR context needed to understand cross-file relationships.

---

## 10.3 — Structured PRPlan

The PR Planner must produce a structured application-level `PRPlan`.

The plan must not be represented solely as free-form text or embedded wholesale into `ReviewRequest.instruction`.

The plan should contain information common to the entire PR and separate file-specific plans.

Conceptually:

```text
PRPlan
├── summary
├── objectives
├── cross_file_considerations
├── execution_constraints
└── file_plans[]
      ├── path
      ├── required
      ├── objectives
      ├── changes[]
      └── dependencies[]
```

The exact schema should be established during implementation, but the following responsibilities are required.

### PR-level fields

PR-level information should describe:

* Overall purpose of the required changes.
* Global objectives.
* Cross-file considerations.
* Architectural or behavioral relationships between changes.
* Constraints that apply to the entire PR.
* Planning assumptions where relevant.

### File-level plans

Each applicable file should have a dedicated plan containing only the information relevant to that file's workflow, while retaining references to cross-file considerations where necessary.

A file plan should be capable of expressing:

* Whether the file requires modification.
* Objectives for the file.
* Required changes.
* Rationale for the changes where useful.
* Dependencies on other changed files.
* Relevant cross-file considerations.

The planner must be able to explicitly determine that a changed file requires no modification.

Files for which the planner determines that no change is necessary must **not** be sent to `CodeWorkflow`.

---

## 10.4 — Planner Responsibilities and Boundaries

The PR Planner is responsible for software-engineering reasoning at the PR level.

It may determine:

* Required changes.
* File relationships.
* Cross-file dependencies.
* Implementation strategy.
* File-specific objectives.
* Ordering constraints.
* Priorities.
* Relevant considerations for individual workflows.

The planner must not:

* Execute tools directly.
* Modify files directly.
* Persist workflow state directly.
* Mutate `PRExecutionState` directly.
* Bypass mandatory workflow stages.
* Change workflow retry limits.
* Change security requirements.
* Disable evaluation.
* Terminate a workflow directly.
* Invent unsupported capabilities.
* Introduce GitHub-specific objects into application models.

The application remains authoritative over execution.

The distinction is:

```text
LLM:
    What should be changed and how should the changes relate?

Application:
    How, when, and under what constraints is the plan executed?
```

---

## 10.5 — Capability and Workflow Contracts

The planner must operate against an application-defined vocabulary of supported capabilities and workflow stages.

Initially, the existing workflow provides the primary execution capabilities:

* Code review.
* Security analysis.
* Refactoring.
* Test generation.
* Test execution.
* Evaluation.

Each capability used by planning must have a stable application-controlled contract.

The LLM must not invent executable capabilities.

The planner should describe desired work through the structured `PRPlan`; deterministic application code is responsible for translating the plan into existing workflow execution.

The existing file workflow remains mandatory:

```text
Reviewer
    ↓
Security Auditor
    ↓
CodeWriter
    ↓
Test Generator
    ↓
Test Executor
    ↓
Evaluator
```

Planner output must not be able to remove mandatory stages.

---

## 10.6 — PR Execution State

Introduce an application-level `PRExecutionState` to coordinate execution of the file-level workflows without immediately introducing a new persistence model.

The initial implementation should keep `PRExecutionState` in memory.

It should track information such as:

* Original `PRPlan`.
* Files selected for processing.
* Completed file workflows.
* Current candidate version of each processed file.
* Workflow results.
* Dependency state.
* Relevant evaluator feedback.
* Whether PR-level replanning is required.

`PRExecutionState` is distinct from individual `WorkflowRun` persistence.

Each file workflow continues to have its own existing workflow identity and persistence boundary.

A PR-level persistence model such as `PRReviewRun` is explicitly deferred unless later requirements justify it.

---

## 10.7 — Dependency-Aware File Execution

File workflows should not be treated as unrelated independent operations.

The PR Planner should identify dependencies between file-level changes.

For example:

```text
service.py
    │
    ├──→ controller.py
    │
    └──→ test_service.py
```

If `controller.py` depends on changes made to `service.py`, the service workflow should execute first.

Execution ordering should therefore be determined primarily by dependencies expressed by the plan.

Where multiple files have no dependency relationship, deterministic secondary ordering may be used. Change size may be used as one possible secondary ordering signal, but it must not override explicit dependencies.

The initial implementation should execute file workflows **sequentially**.

This avoids introducing concurrency complexity before the dependency and cross-file execution model is established.

---

## 10.8 — Updated Cross-File Context

After a file workflow completes, subsequent workflows should be able to reason about the resulting candidate rather than only the original PR state.

For example:

```text
Original service.py
        ↓
Workflow A
        ↓
Candidate service.py
        ↓
Workflow B receives relevant updated context
```

`PRExecutionState` should therefore maintain the current version of completed files.

When a later workflow depends on an already processed file, its context should contain the relevant updated candidate so that the workflow can remain synchronized with previously implemented changes.

The original `PRContext` remains the description of the original PR.

The execution state represents the evolving implementation state.

These concepts must not be conflated.

```text
PRContext
    = what the PR originally contains

PRExecutionState
    = what has happened to the PR during AI processing
```

---

## 10.9 — File Workflow Integration

The existing `CodeWorkflow` remains responsible for implementing the applicable portion of the PR plan.

Each file workflow should receive:

* The complete target file.
* The complete `PRContext`.
* The applicable file-specific plan.
* Relevant updated candidate context from previously completed dependent files.
* The existing workflow configuration.

The workflow continues to own:

* Review.
* Security analysis.
* Refactoring.
* Test generation.
* Test execution.
* Evaluation.
* Existing retry behavior.
* Workflow persistence.
* Workflow failure handling.

The planner does not replace these components.

Instead, it provides coordinated PR-level intent that they execute and validate.

---

## 10.10 — Evaluator Feedback and PR-Level Replanning

Individual Evaluators remain responsible for evaluating their file-level workflow results.

Their output may contain:

* Successful completion with no comments.
* Successful completion with informational findings.
* Actionable findings.
* Implementation failures.
* Test failures.
* Cross-file concerns.

Not every evaluator result should trigger PR-level replanning.

### File-level issues

Ordinary implementation failures should first use the existing file-level retry mechanism.

For example:

```text
File workflow
      ↓
Evaluator failure
      ↓
Existing retry loop
      ↓
Resolved
```

The PR Planner should not be invoked merely because an individual workflow required a retry.

### Cross-file issues

If evaluation identifies an issue that affects the relationship between files or indicates that the current PR plan is incomplete or incorrect, the issue may become PR-level feedback.

For example:

```text
File A:
"Changing this interface requires an update to File B."
```

Such feedback should be aggregated and considered for PR-level replanning.

The application should distinguish ordinary file-level feedback from actionable cross-file feedback.

---

## 10.11 — PR-Level Feedback Aggregation

Introduce an application-level representation for feedback that can be evaluated for PR-level impact.

The initial implementation should not require a separate LLM synthesis agent.

Application logic should collect relevant evaluator results and identify feedback that is potentially cross-file.

Conceptually:

```text
Workflow A ──→ Evaluator A ──┐
Workflow B ──→ Evaluator B ──┼──→ PR-level feedback
Workflow C ──→ Evaluator C ──┘
```

PR-level feedback should preserve enough information to identify:

* Source file.
* Workflow result.
* Finding or comment.
* Relevant severity or classification.
* Cross-file implication.
* Related files where known.

The aggregation mechanism should avoid treating unrelated file-level comments as a single PR-level issue.

A future milestone may introduce an LLM-based PR-level synthesis agent if real workflow results demonstrate that deterministic aggregation is insufficient.

---

## 10.12 — Controlled PR Replanning

If PR-level feedback contains actionable cross-file issues, invoke the PR Planner again.

The second planning invocation must receive sufficient information to understand both the original PR and the work already performed.

The planner should receive:

```text
Original PRContext
+
Original PRPlan
+
Completed workflow results
+
Current candidate versions
+
Actionable PR-level feedback
```

The planner then produces a revised `PRPlan`.

Conceptually:

```text
Original PRPlan
      ↓
File workflows
      ↓
Evaluator feedback
      ↓
Cross-file feedback
      ↓
PRPlanner
      ↓
Revised PRPlan
```

The revised plan must take completed work into account rather than blindly starting from the original repository state.

The application remains responsible for deciding whether replanning is allowed and for enforcing configured limits on planner invocations.

The LLM must not determine its own replanning budget.

---

## 10.13 — Planner Failure and Safety

Define controlled behavior for:

* Planner timeout.
* LLM provider failure.
* Invalid structured output.
* Unsupported plan content.
* Missing required plan fields.
* Contradictory dependencies.
* Excessive context.
* Model unavailability.
* Replanning failure.

A valid initial PR plan is required before any file workflow starts.

Therefore:

```text
PRPlanner failure
        ↓
No file workflows
```

A partially valid plan must not result in arbitrary execution of whichever file plans happened to be successfully parsed.

For replanning failures, application policy must determine whether:

* The current completed state is retained and processing stops.
* A safe deterministic continuation is possible.
* The PR is marked as requiring manual intervention.

The LLM must never silently bypass the planner failure boundary.

---

## 10.14 — Deterministic Plan Validation

Every LLM-generated `PRPlan` must be validated by application-controlled logic before execution.

Validation must verify:

* Required fields are present.
* File paths correspond to the PR's supported changed files.
* A file is not planned for modification unless it belongs to the PR context.
* File-level plans reference valid files.
* Dependencies reference valid planned files.
* Dependencies do not create unsupported execution relationships.
* Mandatory workflow stages remain intact.
* Planner output conforms to the application schema.
* Execution limits are respected.
* Unsupported capabilities are rejected.
* Security and policy constraints are preserved.

Malformed or unsafe plans must not be executed.

Where appropriate, the application may request a new plan or terminate PR processing rather than attempting to repair arbitrary planner output.

---

## 10.15 — Planner Context and Token Management

The planner is intentionally given broad PR context because its purpose is to reason about the PR as a whole.

The initial implementation should provide:

* Complete contents of supported changed files.
* All relevant changed-file metadata.
* All available diffs.
* PR metadata.
* Existing candidate versions and feedback during replanning.

However, context size must remain bounded by application-level limits.

The application should explicitly define limits for:

* Maximum number of changed files.
* Maximum total source size.
* Maximum total diff size.
* Maximum planner input size.
* Maximum planner output size.
* Maximum replanning attempts.

If the PR exceeds configured limits, processing should fail safely rather than silently truncating information required for correct planning.

Future optimization may introduce selective context retrieval, summarization, or dependency-driven context expansion.

---

## 10.16 — Planner Prompt and Structured Output

Define a dedicated PR Planner contract rather than reusing prompts intended for individual file agents.

The planner prompt should establish:

* Its role as a PR-level planning agent.
* The complete context available to it.
* The requirement to reason about cross-file relationships.
* The requirement to produce only structured plan output.
* The distinction between planning and implementation.
* The requirement not to invent unsupported capabilities.
* The requirement to identify files that do not require changes.
* The requirement to identify dependencies explicitly.
* The requirement to preserve behavioral and architectural consistency across files.

Structured output should be schema-validated before entering the execution layer.

The planner should not return executable code as part of the implementation plan.

---

## 10.17 — Agent Collaboration

Use structured contracts between the PR Planner and existing workflow agents.

The initial collaboration model is:

```text
PRPlanner
    ↓
PRPlan
    ↓
File-specific workflow
    ↓
Evaluator
    ↓
PR-level feedback when applicable
    ↓
PRPlanner
```

The existing agents remain specialized:

### PRPlanner

Responsible for:

* Whole-PR reasoning.
* Cross-file planning.
* Change coordination.
* Dependency identification.

### Reviewer

Responsible for:

* Reviewing the target file.
* Assessing the planned change against the actual implementation.
* Identifying issues missed by the PR Planner.

### Security Auditor

Responsible for:

* Independent security analysis.
* Identifying security issues missed by the plan or Reviewer.

### CodeWriter

Responsible for:

* Implementing the applicable file-level plan.
* Incorporating Reviewer and Security Auditor findings.
* Preserving the required cross-file behavior.

### Test Generator

Responsible for:

* Generating tests appropriate to the resulting file behavior.

### Test Executor

Responsible for:

* Executing the generated tests and relevant validation.

### Evaluator

Responsible for:

* Evaluating the resulting implementation.
* Identifying unresolved issues.
* Identifying cross-file concerns when applicable.

No individual specialist agent should be treated as an unquestioned authority over the PR-level plan.

---

## 10.18 — Capability Registry

Maintain an application-controlled registry of capabilities available to the agentic planning system.

Each capability should have:

* Stable identifier.
* Input contract.
* Output contract.
* Execution constraints.
* Safety requirements.

The initial registry should map primarily to capabilities already implemented by the platform.

The LLM must select only from registered capabilities.

Capability expansion should remain an application-controlled change rather than something the planner can introduce dynamically.

---

## 10.19 — Advanced Tool Selection

If justified by the capability registry, allow the PR Planner to identify deterministic tools required by the plan.

Tool selection must remain:

* Application-defined.
* Schema-validated.
* Permission-controlled.
* Observable.
* Auditable.

The planner itself must not directly execute arbitrary tools.

All execution remains under deterministic application control.

---

## 10.20 — PR-Level Persistence

Do not introduce dedicated PR-level persistence as part of the initial Milestone 10 implementation.

Continue to persist individual `WorkflowRun` and related workflow records using the existing persistence model.

`PRPlan` and `PRExecutionState` may initially exist only for the lifetime of the PR processing operation.

A future milestone may introduce a persistent PR-level execution entity if requirements emerge for:

* Reproducibility.
* Long-running PR processing.
* Resume-after-failure.
* Historical PR plans.
* Plan/version comparison.
* Replanning history.
* PR-level analytics.

Any future persistence model must preserve the existing per-file workflow identity rather than replacing it.

---

## 10.21 — Observability and Auditability

Extend observability to cover PR-level planning decisions without exposing secrets or unnecessary external information.

Record appropriate telemetry for:

* Planner invocation.
* Planner latency.
* Planner success/failure.
* Plan validation result.
* Number of planned files.
* Dependency relationships.
* Workflow execution order.
* Replanning invocation.
* Replanning reason.
* Plan revision count.
* Planner token usage where available.
* Context size where available.
* Fallback or termination events.

Do not persist or emit GitHub credentials.

Do not expose raw planner prompts or sensitive source content through externally accessible telemetry unless explicitly required and appropriately protected.

Planner and PR-level trace data must follow the project's existing information-disclosure and trace-sanitization decisions.

---

## 10.22 — Advanced Planning Evaluation

Extend the benchmark framework to evaluate PR-level planning quality.

Measure:

* Plan validity.
* Correct file selection.
* Correct identification of unnecessary files.
* Cross-file consistency.
* Dependency correctness.
* Implementation success.
* Finding resolution.
* Test success.
* Security correctness.
* Maintainability.
* Replanning effectiveness.
* Retry rate.
* Planner invocation count.
* Token usage.
* Latency.
* Context size.
* Plan revision rate.
* Failure rate.

Compare the agentic PR-planning architecture against the deterministic baseline established before Milestone 10.

Evaluation should specifically determine whether PR-level planning improves:

* Cross-file consistency.
* Correctness of coordinated changes.
* Reduction of contradictory file-level changes.
* Ability to resolve issues spanning multiple files.
* Overall workflow efficiency.

Do not retain additional agentic complexity without measurable benefit.

---

## 10.23 — Milestone Validation

Validate the complete PR-level planning architecture.

At minimum:

* Run the complete test suite.
* Run GitHub integration tests.
* Test PRs containing multiple changed files.
* Test PRs where some changed files require no modification.
* Test cross-file dependencies.
* Test sequential dependency-aware execution.
* Test propagation of updated candidate versions.
* Test planner structured-output validation.
* Test planner failure before workflow execution.
* Test individual workflow failures.
* Test evaluator feedback aggregation.
* Test cross-file replanning.
* Test replanning failure.
* Test configured planner/replanning limits.
* Verify mandatory workflow stages cannot be bypassed.
* Verify GitHub credentials remain protected.
* Verify telemetry and trace sanitization.
* Verify persistence of individual workflow runs.
* Verify API compatibility.
* Run the benchmark suite.
* Compare agentic planning results with the deterministic baseline.

### Target end-to-end flow

```text
GitHub PR
    ↓
GitHub Adapter
    ↓
PRContext + complete changed-file contents
    ↓
PRPlanner
    ↓
Structured PRPlan
    ↓
Deterministic plan validation
    ↓
PRExecutionState
    ↓
Dependency-aware sequential execution
    ↓
File-specific CodeWorkflow instances
    ↓
Evaluators
    ↓
PR-level feedback aggregation
    │
    ├── no actionable cross-file feedback
    │        ↓
    │      finish
    │
    └── actionable cross-file feedback
             ↓
          PRPlanner
             ↓
       revised PRPlan
             ↓
       continue execution
```

**Outcome:** The platform can reason about an entire pull request, produce a structured and coordinated implementation plan, execute that plan through the existing deterministic per-file workflows, maintain cross-file execution state, and revise the plan when evaluator feedback identifies actionable cross-file issues.

The resulting architecture combines LLM-based software-engineering reasoning with deterministic application-controlled execution, validation, safety constraints, and existing workflow persistence.
