"""Path normalization and safety checks."""

from __future__ import annotations

from pathlib import Path

from .errors import MCPError


def normalize_path(raw_path: str) -> Path:
    """Resolve a user-supplied path to an absolute path."""
    try:
        return Path(raw_path).expanduser().resolve()
    except Exception as exc:  # pragma: no cover - path parser edge case
        raise MCPError(
            code="INVALID_PATH",
            message="Path could not be normalized.",
            details={"path": raw_path, "reason": str(exc)},
        ) from exc


def ensure_existing_directory(raw_path: str, label: str) -> Path:
    """Require an existing directory path."""
    path = normalize_path(raw_path)
    if not path.exists():
        raise MCPError(
            code="NOT_FOUND",
            message=f"{label} does not exist.",
            details={"path": str(path)},
        )
    if not path.is_dir():
        raise MCPError(
            code="INVALID_PATH",
            message=f"{label} must be a directory.",
            details={"path": str(path)},
        )
    return path


def ensure_project_directory(raw_path: str) -> Path:
    """Require a valid Godot project directory containing project.godot."""
    project_path = ensure_existing_directory(raw_path, "Project path")
    project_file = project_path / "project.godot"
    if not project_file.exists():
        raise MCPError(
            code="INVALID_PROJECT",
            message="project.godot was not found in project path.",
            details={"project_path": str(project_path)},
        )
    return project_path

