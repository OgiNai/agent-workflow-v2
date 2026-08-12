from apps.workflows.retry_policy import should_retry


def test_retry_allowed_before_max_rounds():
    assert should_retry("retry", round_number=1, max_rounds=2) is True


def test_retry_blocked_at_max_rounds():
    assert should_retry("retry", round_number=2, max_rounds=2) is False


def test_pass_does_not_retry():
    assert should_retry("pass", round_number=1, max_rounds=2) is False
