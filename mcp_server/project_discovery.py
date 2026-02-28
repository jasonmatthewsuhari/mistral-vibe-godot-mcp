from __future__ import annotations

from pathlib import Path

from mcp_server.errors import make_error


def discover_projects(root_path: str) -> list[dict[str, str]]:
    root = Path(root_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise make_error("not_found", "Project root path does not exist", {"root_path": str(root)})

    results: list[dict[str, str]] = []
    for project_file in sorted(root.rglob("project.godot")):
        project_dir = project_file.parent
        results.append(
            {
                "name": project_dir.name,
                "path": str(project_dir),
                "project_file": str(project_file),
            }
        )
    return results
