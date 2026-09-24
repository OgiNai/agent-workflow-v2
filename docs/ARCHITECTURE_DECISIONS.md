- planner will be deterministic in the beginning and become an LLM agent at later stage. When   that happens instructions to agents within the retry loop will be tailored

---

- Externally accessible failure information is sanitized. API responses and persisted workflow/step traces expose only controlled, application-generated failure descriptions. Raw exception messages and tracebacks remain internal to logging and telemetry.

  This prevents accidental disclosure of internal infrastructure details, filesystem paths, database/provider information, credentials, or user-controlled data through externally accessible workflow state.

  Failure information follows this boundary:

                      ┌── logs ──────────────── raw exception + traceback
  Exception ──────────┤
                      ├── telemetry ────────── exception event/details
                      │
                      └── API / persisted ──── sanitized failure description

  Raw exception details must not be included in ReviewResponse, WorkflowRun summaries, or WorkflowStepTrace details. Safe, application-generated descriptions such as "Agent execution failed." may be exposed.

---

- A workflow failure at any retry round must persist all successfully completed steps from previous rounds and the current round's failed step before returning the failed workflow state.

---

# Automated Test Suite Independence:

The standard automated test suite must be deterministic and runnable without external LLM access. Workflow and API tests use dependency injection and mocks to isolate external LLM/provider dependencies while exercising the application's real workflow, persistence, and API boundaries.

LLM-dependent acceptance or smoke tests, if introduced later, are separate from the standard test suite and are not required for normal CI/test-suite execution.

---

# Environment Configuration

APP_ENV identifies the runtime environment as one of development, test, or production.

The application uses the same configuration models across all environments. Environment-specific behavior is controlled by supplying different configuration values rather than maintaining separate development, test, and production settings classes.

---

# Generated-code execution security boundary

Generated Python code is currently executed in a temporary working directory with timeout control, but without OS/container-level sandboxing. Therefore generated-code execution must be treated as untrusted code execution and is not considered securely isolated from the application host. Strong isolation is a future deployment/execution-boundary concern.

---

# GitHub Integration Boundary

GitHub is treated as an external infrastructure adapter and is intentionally kept separate from the core workflow and application/domain logic. `CodeWorkflow` must remain independent of GitHub-specific concepts. The initial GitHub integration processes supported changed files as independent workflow inputs. Each supported file can therefore have its own `workflow_run_id`, persistence history, evaluation, and failure boundary. Unsupported file types are filtered by the GitHub integration and are not treated as workflow failures. 

ReviewRequest is composed by content of changed file as code field and the cnanges (PR/diff) in the review_context field containing an application-level context model. Context models contain external or task-specific information required to perform specific operation and must remain independent of external provider types. For example, PRContext must not contain GitHubPullRequest or GitHubChangedFile objects. The GitHub integration maps GitHub-specific models into the application-level context before creating a ReviewRequest.

GitHub authentication and credentials remain inside the integration/infrastructure boundary and must never be passed into `CodeWorkflow` or persisted as workflow data.

---

# PRContext is PR-level context

A GitHub pull request may produce multiple independent ReviewRequest instances and corresponding workflow runs—one for each supported changed file. Each ReviewRequest contains the complete current contents of its target file in code, while its review_context references the PR-level PRContext. PRContext represents the context of an entire pull request, not the context of an individual changed file.

PRContext contains pull-request metadata and the complete changed-file manifest, including metadata and diffs for all changed files. This allows Reviewer and Security Auditor agents processing one target file to reason about related changes elsewhere in the same pull request without making CodeWorkflow GitHub-aware.

---

