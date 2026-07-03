from apps.schemas.agent_outputs import EvaluatorOutput
from apps.workflows.retry_policy import should_retry


def make_eval(decision: str):
    return EvaluatorOutput(
        final_decision=decision,
        rule_score=0.5,
        execution_score=0.5,
        llm_score=0.5,
        security_score=0.5,
        maintainability_score=0.5,
        correctness_score=0.5,
        final_score=0.5,
        reasons=[],
    )


def test_retry_allowed_before_max_rounds():
    assert should_retry(make_eval("retry"), round_number=1, max_rounds=2) is True


def test_retry_blocked_at_max_rounds():
    assert should_retry(make_eval("retry"), round_number=2, max_rounds=2) is False


def test_pass_does_not_retry():
    assert should_retry(make_eval("pass"), round_number=1, max_rounds=2) is False
