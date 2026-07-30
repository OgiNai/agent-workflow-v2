from pathlib import Path
from uuid import UUID

from apps.core.constants import REVIEW_RUNS_DIR_NAME, WORKSPACE_DIR_NAME
from apps.core.settings import get_auth_settings


def get_project_root() -> Path:
    return Path(get_auth_settings().project_path).resolve()


def resolve_project_file_path(file_path: str) -> Path:
    root = get_project_root()
    target = (root / file_path).resolve()

    if not target.is_relative_to(root):
        raise ValueError("Path escapes the allowed project directory.")

    return target

def get_workspace_run_dir(workflow_run_id: UUID | str) -> Path:
    """Return workspace/review_runs/{workflow_run_id}, creating it if needed."""
    run_dir = (
        get_project_root()
        / WORKSPACE_DIR_NAME
        / REVIEW_RUNS_DIR_NAME
        / str(workflow_run_id)
    ).resolve()

    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def resolve_artifact_path(workflow_run_id: UUID | str, relative_path: str) -> Path:
    """Resolve an artifact path inside the workflow run workspace."""
    run_dir = get_workspace_run_dir(workflow_run_id)
    target = (run_dir / relative_path).resolve()

    if not target.is_relative_to(run_dir):
        raise ValueError("Artifact path escapes workflow workspace.")

    return target