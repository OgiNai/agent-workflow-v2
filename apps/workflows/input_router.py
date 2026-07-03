"""Deterministic input router for the unified workflow."""

import re
from typing import Literal

from apps.schemas.requests import ReviewRequest
from apps.schemas.workflow import RouterResult
from apps.tools.safe_file_reader import read_project_file

_CODE_FENCE_RE = re.compile(r"```(?:python|py)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def extract_markdown_code(text: str) -> str | None:
    match = _CODE_FENCE_RE.search(text)
    if not match:
        return None
    return match.group(1).strip()


def looks_like_python_code(text: str) -> bool:
    """Small heuristic; explicit request fields should be preferred over this."""
    stripped = text.strip()
    if "\n" in stripped and any(token in stripped for token in ("def ", "class ", "import ", "from ", "return ")):
        return True
    return stripped.startswith(("def ", "class ", "import ", "from ", "@"))


def _resolve_task_type(request: ReviewRequest, resolved_input_type: str) -> Literal["generate", "review", "refactor", "review_refactor"]:
    if request.task_type != "auto":
        if request.task_type == "review":
            return "review"
        if request.task_type == "refactor":
            return "refactor"
        if request.task_type == "review_refactor":
            return "review_refactor"
        return "generate"

    if resolved_input_type in {"inline_code", "file_path"}:
        return "review_refactor"
    return "generate"


def route_input(request: ReviewRequest) -> RouterResult:
    """Normalize raw API input before PlannerAgent is called."""
    content = request.content or ""

    if request.file_path or request.input_type == "file_path":
        if not request.file_path:
            raise ValueError("file_path is required for file_path input.")
        tool_result = read_project_file(request.file_path)
        if tool_result.status == "failed":
            raise ValueError(tool_result.error or "Failed to read file.")
        task_type = _resolve_task_type(request, "file_path")
        return RouterResult(
            task_type=task_type,
            input_type="file_path",
            instruction=request.instruction,
            code_available=True,
            code=tool_result.output,
            source_path=request.file_path,
            original_content=tool_result.output,
        )

    code_block = extract_markdown_code(content)
    if code_block:
        task_type = _resolve_task_type(request, "inline_code")
        return RouterResult(
            task_type=task_type,
            input_type="inline_code",
            instruction=request.instruction,
            code_available=True,
            code=code_block,
            original_content=content,
        )

    if request.input_type == "inline_code" or looks_like_python_code(content):
        task_type = _resolve_task_type(request, "inline_code")
        return RouterResult(
            task_type=task_type,
            input_type="inline_code",
            instruction=request.instruction,
            code_available=True,
            code=content,
            original_content=content,
        )

    task_type = _resolve_task_type(request, "natural_language")
    return RouterResult(
        task_type=task_type,
        input_type="natural_language",
        instruction=request.instruction,
        code_available=False,
        code=None,
        original_content=content,
    )
