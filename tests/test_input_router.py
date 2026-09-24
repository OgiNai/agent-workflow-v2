from apps.schemas.requests import ReviewRequest
from apps.workflows.input_router import (
    _extract_markdown_code,
    route_input,
)


def test_extract_markdown_code():
    text = "Please review:\n```python\ndef add(a, b):\n    return a + b\n```"
    assert _extract_markdown_code(text).startswith("def add")


def test_auto_inline_code_routes_to_review_refactor():
    request = ReviewRequest(
        instruction="Review this",
        code="def div(a, b):\n    return a / b",
    )
    result = route_input(request)
    assert result.task_type == "review_refactor"
    assert result.code_available is True

    assert request.review_context is None


def test_auto_natural_language_routes_to_generate():
    request = ReviewRequest(
        instruction="Create a Python function that safely divides two numbers.",
    )
    result = route_input(request)
    assert result.task_type == "generate"
    assert result.code_available is False
