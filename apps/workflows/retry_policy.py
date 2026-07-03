"""Retry policy for the quality loop."""

from apps.schemas.agent_outputs import EvaluatorOutput


def should_retry(evaluation: EvaluatorOutput, round_number: int, max_rounds: int) -> bool:
    return evaluation.final_decision == "retry" and round_number < max_rounds
