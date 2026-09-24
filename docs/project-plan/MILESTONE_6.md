# Milestone 6 — GitHub Integration

**Goal:** Integrate GitHub as an external adapter while keeping GitHub-specific concerns isolated from the core workflow and domain logic.

## 6.1 — GitHub Integration Architecture

* Define GitHub as an external adapter around the existing workflow.
* Keep `CodeWorkflow` independent of GitHub APIs.
* Define the boundary between:

  * GitHub repository data.
  * Application/domain models.
  * `ReviewRequest`.
  * `ReviewResponse`.
* Define which GitHub operations belong to the MVP.
* Defer non-essential GitHub functionality.
* Define security and permission boundaries before implementation.

Target architecture:

```text
GitHub API
        ↓
GitHub Adapter
        ↓
ReviewRequest
        ↓
CodeWorkflow
        ↓
ReviewResponse
        ↓
GitHub Adapter
        ↓
GitHub API
```

## 6.2 — GitHub Authentication

* Select the authentication mechanism appropriate for the MVP.
* Store GitHub credentials using the existing configuration and secret-management approach.
* Never expose credentials through API responses, logs, traces, benchmark reports, or persisted workflow data.
* Define minimum required GitHub permissions.
* Validate authentication configuration.
* Handle expired, invalid, or insufficient credentials safely.

## 6.3 — Repository and File Access

Implement isolated GitHub operations for:

* Repository identification.
* Branch/ref selection.
* File retrieval.
* Repository metadata.
* Changed-file discovery where required.

Map GitHub-specific responses into application-level models.

Use the existing httpx2 dependency rather than introducing PyGithub.

Do not allow GitHub SDK/API types to leak into the workflow layer.

## 6.4 — Pull Request Review

Support the core GitHub pull-request review flow while preserving the existing
file-level workflow and persistence boundaries.

```text
                         GitHub Pull Request
                                  │
                 ┌────────────────┴────────────────┐
                 │                                 │
           PR metadata                      changed files
                 │                                 │
                 └────────────────┬────────────────┘
                                  ▼
                              PRContext
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
               ReviewRequest  ReviewRequest  ReviewRequest
                  file A         file B         file C
                  code=A         code=B         code=C
                  context=PR    context=PR    context=PR
                    │             │             │
                    ▼             ▼             ▼
                Workflow A     Workflow B     Workflow C
                    │             │             │
                    ▼             ▼             ▼
               workflow_run   workflow_run   workflow_run
```

* Define the PR-level context shared by all per-file review requests. Define PRContext as PR-specific rather than file-specific.
* Preserve complete current source code for each target file in ReviewRequest.code.
* Include metadata and diffs for all changed files in PRContext, without duplicating complete source contents across requests.
* Define how multiple changed files are mapped to independent ReviewRequest instances and workflow runs.
* Provide PR context to Reviewer and Security Auditor without making CodeWorkflow GitHub-aware.
* Keep ordinary non-GitHub ReviewRequest instances valid with review_context=None.

## 6.5 — GitHub Review Comments

Map normalized findings to GitHub review comments where technically possible.

Each comment should preserve:

* Finding ID.
* Severity.
* File path.
* Line information.
* Review message.
* Workflow-run reference where appropriate.

Handle findings that cannot be mapped cleanly to a source line.

## 6.6 — GitHub Integration Testing

* Mock GitHub API interactions.
* Test authentication failures.
* Test repository/file retrieval failures.
* Test malformed GitHub responses.
* Test pull requests with multiple files.
* Test findings-to-comment mapping.
* Ensure tests do not depend on a real GitHub repository.

## 6.7 — Milestone Validation

Verify the complete integration:

```text
GitHub PR
    ↓
GitHub adapter
    ↓
AI workflow
    ↓
Evaluation
    ↓
Findings
    ↓
GitHub review
```

**Outcome:** The platform can process GitHub-based code reviews without coupling the core workflow to GitHub.