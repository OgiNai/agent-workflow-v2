"""Artifact helpers for workflow runs."""

from uuid import UUID

from apps.schemas.workflow import ArtifactInfo
from apps.tools.safe_file_writer import write_artifact


def save_artifact(workflow_run_id: UUID, artifact_type: str, relative_path: str, content: str) -> ArtifactInfo:
    result = write_artifact(workflow_run_id, relative_path, content)
    if result.status == "failed":
        raise RuntimeError(result.error or "Artifact write failed")
    return ArtifactInfo(
        artifact_type=artifact_type,
        path=result.output or "",
        size_bytes=result.metadata.get("size_bytes"),
        content_hash=result.metadata.get("content_hash"),
    )
