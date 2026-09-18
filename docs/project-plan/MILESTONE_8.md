# Milestone 8 — API and User Experience

**Goal:** Improve usability and provide a clear interface for demonstrating the complete platform without compromising the API-first architecture.

## 8.1 — Workflow Status and History API

Add API capabilities for:

* Workflow status.
* Workflow history.
* Workflow details.
* Agent-step history.
* Findings.
* Evaluation results.
* Generated artifacts.
* Feedback.

Reuse existing persistence structures where practical.

## 8.2 — API Contract Refinement

Review the public API for:

* Consistent request/response schemas.
* Error responses.
* Authentication.
* Validation errors.
* Workflow identifiers.
* Pagination where needed.
* Backward compatibility.

Only introduce new request fields when they represent genuine user-facing capabilities.

## 8.3 — Developer Experience

Improve:

* API documentation.
* OpenAPI descriptions.
* Example requests.
* Example responses.
* Local development instructions.
* Deployment instructions.
* Architecture documentation.

Provide representative examples for:

* Feature generation.
* Code review/refactoring.
* GitHub review.

## 8.4 — Streamlit Dashboard

Implement the dashboard only after the API and backend are stable.

The dashboard should provide:

```text
Submit workflow
      ↓
View workflow status
      ↓
View generated/refactored code
      ↓
View findings
      ↓
View tests
      ↓
View evaluation
      ↓
View workflow history
```

## 8.5 — Observability View

Expose useful, non-sensitive workflow information such as:

* Agent execution sequence.
* Round number.
* Latency.
* Evaluation score.
* Retry count.
* Token usage.
* Final decision.

Do not expose secrets or unnecessary internal infrastructure details.

## 8.6 — UX Validation

Test the complete user journey:

```text
User
 ↓
API / Dashboard
 ↓
Workflow
 ↓
Evaluation
 ↓
Result
```

**Outcome:** The platform has a usable API and optional demonstration UI suitable for recruiters, developers and portfolio presentation.
