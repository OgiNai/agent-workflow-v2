"""Safe artifact writer tool."""

import hashlib
import time
from uuid import UUID

from apps.core.constants import ALLOWED_WRITE_EXTENSIONS

#from apps.core.settings import get_auth_settings
from apps.schemas.tools import ToolResult
from apps.tools.file_path_helpers import resolve_artifact_path


def write_artifact(workflow_run_id: UUID | str, relative_path: str, content: str) -> ToolResult:
    """Write an artifact into workspace/review_runs/{workflow_run_id}/ only."""
    started = time.perf_counter()
    try:
        target = resolve_artifact_path(workflow_run_id, relative_path)
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
