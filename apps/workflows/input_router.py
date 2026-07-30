"""Deterministic input router for the unified workflow."""

import re

# from typing import Literal
from apps.schemas.requests import ReviewRequest
from apps.schemas.workflow import ResolvedTaskType, RouterResult
from apps.tools.safe_file_reader import read_project_file

_CODE_FENCE_RE = re.compile(r"```(?:python|py)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def _extract_markdown_code(text: str) -> str | None:
    """Extract the first fenced Python code block from text."""
    match = _CODE_FENCE_RE.search(text)
    if not match:
        return None
    return match.group(1).strip()


# def _looks_like_python_code(text: str) -> bool:
#    """Small heuristic; explicit request fields should be preferred over this."""
#    stripped = text.strip()
#    if "\n" in stripped and any(token in stripped for token in ("def ", "class ", "import ", "from ", "return ")):
#        return True
#    return stripped.startswith(("def ", "class ", "import ", "from ", "@"))


# def _resolve_task_type(request: ReviewRequest, resolved_input_type: str) -> Literal["generate", "review_refactor"]:
#    if request.task_type != "auto":
#        return request.task_type
#
#    if resolved_input_type in {"inline_code", "file_path"}:
#        return "review_refactor"
#    return "generate"


def route_input(request: ReviewRequest) -> RouterResult:
    """Normalize raw API input before PlannerAgent is called."""
    if request.file_path:
        file_result = read_project_file(request.file_path)

        if file_result.status == "failed":
            raise ValueError(file_result.error or "Failed to read source file.")

        source_type = "file_path"
        source_code = file_result.output
        source_path = request.file_path

    elif request.code:
        source_type = "inline_code"
        source_code = _extract_markdown_code(request.code) or request.code
        source_path = None

    else:
        source_type = "none"
        source_code = None
        source_path = None

    if request.task_type == "auto":
        task_type: ResolvedTaskType = (
            "review_refactor" if source_code is not None else "generate"
        )
    else:
        task_type = request.task_type

    return RouterResult(
        task_type=task_type,
        source_type=source_type,
        instruction=request.instruction,
        code_available=source_code is not None,
        code=source_code,
        source_path=source_path,
    )
