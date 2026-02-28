"""Pydantic schemas for MCP tool inputs and outputs."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class GodotGetVersionRequest(BaseModel):
    """Input schema for version lookup."""


class GodotGetVersionResponse(BaseModel):
    """Output schema for version lookup."""

    version: str
    path: str


class ProjectInfo(BaseModel):
    """Godot project metadata."""

    name: str
    path: str
    project_file: str


class GodotListProjectsRequest(BaseModel):
    """Input schema for recursive project discovery."""

    root_path: str = Field(min_length=1)


class GodotListProjectsResponse(BaseModel):
    """Output schema for project discovery."""

    projects: list[ProjectInfo]


class GodotLaunchEditorRequest(BaseModel):
    """Input schema for launching Godot editor."""

    project_path: str = Field(min_length=1)
    headless: bool = False


class GodotLaunchEditorResponse(BaseModel):
    """Output schema for launching Godot editor."""

    session_id: str
    pid: int
    status: Literal["running", "exited"]


class GodotRunProjectRequest(BaseModel):
    """Input schema for running a Godot project."""

    project_path: str = Field(min_length=1)
    debug: bool = True
    scene_override: str | None = None


class GodotRunProjectResponse(BaseModel):
    """Output schema for running a project."""

    session_id: str
    pid: int
    status: Literal["running", "exited"]


class GodotStopExecutionRequest(BaseModel):
    """Input schema for stopping running Godot processes."""

    session_id: str | None = None


class GodotStopExecutionResponse(BaseModel):
    """Output schema for process stop results."""

    stopped: bool
    exit_code: int | None = None


class DebugOutputEntry(BaseModel):
    """One captured log line from a managed process."""

    cursor: int
    timestamp: str
    stream: Literal["stdout", "stderr", "system"]
    message: str


class GodotGetDebugOutputRequest(BaseModel):
    """Input schema for debug output retrieval."""

    session_id: str | None = None
    limit: int = Field(default=200, ge=1, le=1000)
    cursor: int | None = Field(default=None, ge=0)


class GodotGetDebugOutputResponse(BaseModel):
    """Output schema for debug output retrieval."""

    entries: list[DebugOutputEntry]
    next_cursor: int | None = None


class GodotAnalyzeProjectRequest(BaseModel):
    """Input schema for project analysis."""

    project_path: str = Field(min_length=1)


class GodotAnalyzeProjectResponse(BaseModel):
    """Output schema for project analysis."""

    scenes: list[str]
    scripts: list[str]
    resources: list[str]
    autoloads: dict[str, str]
    plugins: list[str]
    main_scene: str | None = None

    @field_validator("scenes", "scripts", "resources", "plugins")
    @classmethod
    def sort_paths(cls, values: list[str]) -> list[str]:
        """Normalize deterministic ordering."""
        return sorted(values)

