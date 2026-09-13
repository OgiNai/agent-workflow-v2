from apps.core.constants import DEFAULT_MAX_ROUNDS
from apps.core.settings import get_workflow_settings
from apps.core.workflow_config import WorkflowConfig
from apps.schemas.requests import ReviewRequest


def test_workflow_config_uses_central_default_max_rounds():
    workflow_settings = get_workflow_settings()
    config = WorkflowConfig(
        max_rounds=workflow_settings.workflow_max_rounds,
        force_retry_rounds=workflow_settings.workflow_force_retry_rounds,
        always_retry=workflow_settings.workflow_always_retry,
    )

    assert config.max_rounds == DEFAULT_MAX_ROUNDS


def test_review_request_does_not_override_workflow_settings_when_omitted():
    request = ReviewRequest(instruction="Generate a function")

    assert request.max_rounds is None


def test_review_request_accepts_explicit_max_rounds():
    request = ReviewRequest(
        instruction="Generate a function",
        max_rounds=4,
    )

    assert request.max_rounds == 4
