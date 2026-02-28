from pathlib import Path

import pytest

from mcp_server.errors import MCPError
from mcp_server.project_discovery import discover_projects


def test_discover_projects_finds_nested_project_files(tmp_path: Path) -> None:
    first = tmp_path / "first_project"
    second = tmp_path / "nested" / "second_project"
    first.mkdir()
    second.mkdir(parents=True)
    (first / "project.godot").write_text("[gd_project]\n", encoding="utf-8")
    (second / "project.godot").write_text("[gd_project]\n", encoding="utf-8")

    projects = discover_projects(str(tmp_path))

    assert [p["name"] for p in projects] == ["first_project", "second_project"]


def test_discover_projects_raises_on_missing_root(tmp_path: Path) -> None:
    with pytest.raises(MCPError) as exc:
        discover_projects(str(tmp_path / "missing"))
    assert exc.value.code == "not_found"
    assert "root_path" in exc.value.details
