from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class WorkflowConfig:
    max_rounds: int

    # Debug options (development only)
    force_retry_rounds: int  # for testing multiple rounds execution
    always_retry: bool  # for testing max_rounds exhaustion
