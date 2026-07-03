"""Score aggregation helpers."""


def weighted_final_score(rule_score: float, execution_score: float, llm_score: float) -> float:
    return round((0.25 * rule_score) + (0.45 * execution_score) + (0.30 * llm_score), 3)
