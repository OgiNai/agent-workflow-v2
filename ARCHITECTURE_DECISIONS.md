- planner will be deterministic in the beginning and become an LLM agent at later stage. When   that happens instructions to agents within the retry loop will be tailored

- External failure information is sanitized. API responses and persisted workflow/step traces expose controlled, application-generated failure messages; raw exception messages and tracebacks remain internal to logging/telemetry. Keep exception details out of ReviewResponse to prevent sensitive information disclosure through API and keep it only in private logging channels:

                    ┌── logs ──────────────── full exception + traceback
Exception ──────────┤
                    ├── telemetry ─────────── exception event/details
                    │
                    └── API response ─────── safe failure description 

- 