"""Safe artifact writer tool."""

import hashlib
import time
from pathlib import Path
from uuid import UUID

from apps.core.constants import ALLOWED_WRITE_EXTENSIONS, REVIEW_RUNS_DIR_NAME, WORKSPACE_DIR_NAME
from apps.settings import get_auth_settings
from apps.tools.tool_result import ToolResult


def get_workspace_run_dir(workflow_run_id: UUID | str) -> Path:
    project_root = Path(get_auth_settings().project_path).resolve()
    run_dir = project_root / WORKSPACE_DIR_NAME / REVIEW_RUNS_DIR_NAME / str(workflow_run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir.resolve()


def write_artifact(workflow_run_id: UUID | str, relative_path: str, content: str) -> ToolResult:
    """Write an artifact into workspace/review_runs/{workflow_run_id}/ only."""
    started = time.perf_counter()
    try:
        run_dir = get_workspace_run_dir(workflow_run_id)
        target = (run_dir / relative_path).resolve()
        if not target.is_relative_to(run_dir):
            raise ValueError("Artifact path escapes workflow workspace.")
        if target.suffix not in ALLOWED_WRITE_EXTENSIONS:
            raise ValueError(f"Unsupported artifact extension: {target.suffix}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        return ToolResult(
            tool_name="safe_file_writer",
            status="success",
            output=str(target),
            latency_ms=int((time.perf_counter() - started) * 1000),
            metadata={
                "path": str(target),
                "size_bytes": len(content.encode("utf-8")),
                "content_hash": digest,
            },
        )
    except Exception as exc:
        return ToolResult(
            tool_name="safe_file_writer",
            status="failed",
            error=str(exc),
            latency_ms=int((time.perf_counter() - started) * 1000),
            metadata={"relative_path": relative_path},
        )
