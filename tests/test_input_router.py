from apps.schemas.requests import ReviewRequest
from apps.workflows.input_router import extract_markdown_code, looks_like_python_code, route_input


def test_extract_markdown_code():
    text = "Please review:\n```python\ndef add(a, b):\n    return a + b\n```"
    assert extract_markdown_code(text).startswith("def add")


def test_looks_like_python_code():
    assert looks_like_python_code("def div(a, b):\n    return a / b") is True
    assert looks_like_python_code("Create a function that divides numbers") is False


def test_auto_inline_code_routes_to_review_refactor():
    request = ReviewRequest(
        instruction="Review this",
        content="def div(a, b):\n    return a / b",
    )
    result = route_input(request)
    assert result.task_type == "review_refactor"
    assert result.input_type == "inline_code"
    assert result.code_available is True


def test_auto_natural_language_routes_to_generate():
    request = ReviewRequest(
        instruction="Create a safe divide function",
        content="Create a Python function that safely divides two numbers.",
    )
    result = route_input(request)
    assert result.task_type == "generate"
    assert result.input_type == "natural_language"
    assert result.code_available is False
