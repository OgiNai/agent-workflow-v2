- planner will be deterministic in the beginning and become an LLM agent at later stage. When   that happens instructions to agents within the retry loop will be tailored

- Externally accessible failure information is sanitized. API responses and persisted workflow/step traces expose only controlled, application-generated failure descriptions. Raw exception messages and tracebacks remain internal to logging and telemetry.

  This prevents accidental disclosure of internal infrastructure details, filesystem paths, database/provider information, credentials, or user-controlled data through externally accessible workflow state.

  Failure information follows this boundary:

                      ┌── logs ──────────────── raw exception + traceback
  Exception ──────────┤
                      ├── telemetry ────────── exception event/details
                      │
                      └── API / persisted ──── sanitized failure description

  Raw exception details must not be included in ReviewResponse, WorkflowRun summaries, or WorkflowStepTrace details. Safe, application-generated descriptions such as "Agent execution failed." may be exposed.

- A workflow failure at any retry round must persist all successfully completed steps from previous rounds and the current round's failed step before returning the failed workflow state.

