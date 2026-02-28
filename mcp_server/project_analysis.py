"""Godot project discovery and static analysis helpers."""

from __future__ import annotations

import configparser
import os
from pathlib import Path

from .errors import MCPError
from .models import GodotAnalyzeProjectResponse, ProjectInfo
from .pathing import ensure_existing_directory, ensure_project_directory

SCENE_EXTENSIONS = {".tscn", ".scn"}
SCRIPT_EXTENSIONS = {".gd", ".cs", ".py", ".gdshader"}
RESOURCE_EXTENSIONS = {
    ".res",
    ".tres",
    ".material",
    ".mesh",
    ".png",
    ".jpg",
    ".jpeg",
    ".wav",
    ".ogg",
    ".mp3",
}


def list_projects(root_path_raw: str) -> list[ProjectInfo]:
    """Recursively discover Godot projects under an explicit root path."""
    root_path = ensure_existing_directory(root_path_raw, "Root path")
    projects: list[ProjectInfo] = []
    for walk_root, dirs, files in os.walk(root_path):
        if "project.godot" in files:
            project_dir = Path(walk_root)
            projects.append(
                ProjectInfo(
                    name=project_dir.name,
                    path=str(project_dir),
                    project_file=str(project_dir / "project.godot"),
                )
            )
            dirs[:] = []
            continue

        dirs[:] = [d for d in dirs if d not in {".git", ".godot", "__pycache__"}]
    projects.sort(key=lambda p: p.path.lower())
    return projects


def analyze_project(project_path_raw: str) -> GodotAnalyzeProjectResponse:
    """Collect project metadata for scenes, scripts, resources, and plugins."""
    project_path = ensure_project_directory(project_path_raw)
    project_file = project_path / "project.godot"

    config = configparser.ConfigParser(interpolation=None, strict=False)
    try:
        config.read(project_file, encoding="utf-8")
    except Exception as exc:
        raise MCPError(
            code="PROJECT_PARSE_FAILED",
            message="Failed to parse project.godot.",
            details={"project_file": str(project_file), "reason": str(exc)},
        ) from exc

    scenes: list[str] = []
    scripts: list[str] = []
    resources: list[str] = []
    plugins: list[str] = []

    for walk_root, dirs, files in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in {".git", ".godot", "__pycache__"}]
        root = Path(walk_root)
        for filename in files:
            suffix = Path(filename).suffix.lower()
            full_path = root / filename
            relative = full_path.relative_to(project_path).as_posix()
            if suffix in SCENE_EXTENSIONS:
                scenes.append(relative)
            elif suffix in SCRIPT_EXTENSIONS:
                scripts.append(relative)
            elif suffix in RESOURCE_EXTENSIONS:
                resources.append(relative)

            if filename == "plugin.cfg" or suffix == ".gdextension":
                plugins.append(relative)

    autoloads: dict[str, str] = {}
    if config.has_section("autoload"):
        autoloads = {key: value.strip('"') for key, value in config.items("autoload")}

    main_scene = None
    if config.has_section("application"):
        main_scene = config.get("application", "run/main_scene", fallback=None)
        if main_scene:
            main_scene = main_scene.strip('"')

    return GodotAnalyzeProjectResponse(
        scenes=scenes,
        scripts=scripts,
        resources=resources,
        autoloads=autoloads,
        plugins=plugins,
        main_scene=main_scene,
    )

