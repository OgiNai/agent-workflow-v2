"""Safe file reader tool."""

import time

# from pathlib import Path
from apps.core.constants import ALLOWED_READ_EXTENSIONS, MAX_FILE_SIZE_BYTES

# from apps.core.settings import get_auth_settings
from apps.schemas.tools import ToolResult
from apps.tools.file_path_helpers import resolve_project_file_path


def read_project_file(file_path: str) -> ToolResult:
    """Read a file inside PROJECT_PATH with extension and size limits."""
    started = time.perf_counter()
    try:
        target = resolve_project_file_path(file_path)
        if target.suffix not in ALLOWED_READ_EXTENSIONS:
            raise ValueError(f"Unsupported file extension: {target.suffix}")
        if not target.exists() or not target.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")
        size_bytes = target.stat().st_size
        if size_bytes > MAX_FILE_SIZE_BYTES:
            raise ValueError(f"File too large: {size_bytes} bytes")
        content = target.read_text(encoding="utf-8")
        return ToolResult(
            tool_name="safe_file_reader",
            status="success",
            output=content,
            latency_ms=int((time.perf_counter() - started) * 1000),
            metadata={"path": str(target), "size_bytes": size_bytes},
        )
    except OSError as exc:
        return ToolResult(
            tool_name="safe_file_reader",
            status="failed",
            error=str(exc),
            latency_ms=int((time.perf_counter() - started) * 1000),
            metadata={"file_path": file_path},
        )
