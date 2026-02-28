"""MCP tool implementations for core Godot workflows."""

from __future__ import annotations

import asyncio
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Coroutine

from pydantic import BaseModel, ValidationError

from .errors import MCPError
from .godot_discovery import discover_godot_executable
from .models import (
    GodotAnalyzeProjectRequest,
    GodotAnalyzeProjectResponse,
    GodotGetDebugOutputRequest,
    GodotGetDebugOutputResponse,
    GodotGetVersionRequest,
    GodotGetVersionResponse,
    GodotLaunchEditorRequest,
    GodotLaunchEditorResponse,
    GodotListProjectsRequest,
    GodotListProjectsResponse,
    GodotRunProjectRequest,
    GodotRunProjectResponse,
    GodotStopExecutionRequest,
    GodotStopExecutionResponse,
)
from .pathing import ensure_project_directory
from .process_registry import ProcessRegistry
from .project_analysis import analyze_project, list_projects


@dataclass(slots=True)
class ToolDefinition:
    """Metadata and implementation wiring for an MCP tool."""

    name: str
    description: str
    request_model: type[BaseModel]
    response_model: type[BaseModel]
    handler: Callable[[BaseModel], Coroutine[Any, Any, BaseModel]]


class GodotToolService:
    """Stateful service that backs MCP tool handlers."""

    def __init__(self) -> None:
        self.process_registry = ProcessRegistry()

    def get_definitions(self) -> dict[str, ToolDefinition]:
        """Return registry of supported tools for MCP exposure."""
        return {
            "godot_get_version": ToolDefinition(
                name="godot_get_version",
                description="Get installed Godot version and resolved executable path.",
                request_model=GodotGetVersionRequest,
                response_model=GodotGetVersionResponse,
                handler=self.godot_get_version,
            ),
            "godot_list_projects": ToolDefinition(
                name="godot_list_projects",
                description="Recursively list Godot projects beneath a root directory.",
                request_model=GodotListProjectsRequest,
                response_model=GodotListProjectsResponse,
                handler=self.godot_list_projects,
            ),
            "godot_launch_editor": ToolDefinition(
                name="godot_launch_editor",
                description="Launch Godot editor for a project and return session details.",
                request_model=GodotLaunchEditorRequest,
                response_model=GodotLaunchEditorResponse,
                handler=self.godot_launch_editor,
            ),
            "godot_run_project": ToolDefinition(
                name="godot_run_project",
                description="Run a Godot project and return session details.",
                request_model=GodotRunProjectRequest,
                response_model=GodotRunProjectResponse,
                handler=self.godot_run_project,
            ),
            "godot_stop_execution": ToolDefinition(
                name="godot_stop_execution",
                description="Stop a running Godot process by session_id or latest session.",
                request_model=GodotStopExecutionRequest,
                response_model=GodotStopExecutionResponse,
                handler=self.godot_stop_execution,
            ),
            "godot_get_debug_output": ToolDefinition(
                name="godot_get_debug_output",
                description="Read buffered stdout/stderr from a session with cursor pagination.",
                request_model=GodotGetDebugOutputRequest,
                response_model=GodotGetDebugOutputResponse,
                handler=self.godot_get_debug_output,
            ),
            "godot_analyze_project": ToolDefinition(
                name="godot_analyze_project",
                description="Analyze project scenes/scripts/resources/plugins/autoloads/main scene.",
                request_model=GodotAnalyzeProjectRequest,
                response_model=GodotAnalyzeProjectResponse,
                handler=self.godot_analyze_project,
            ),
        }

    async def godot_get_version(self, request: GodotGetVersionRequest) -> GodotGetVersionResponse:
        del request
        godot_path = discover_godot_executable()

        def _run_version(path: Path) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                [str(path), "--version"],
                capture_output=True,
                text=True,
                timeout=8,
                check=False,
            )

        result = await asyncio.to_thread(_run_version, godot_path)
        version = (result.stdout or result.stderr).strip()
        if not version:
            raise MCPError(
                code="GODOT_VERSION_FAILED",
                message="Failed to read Godot version output.",
                details={"path": str(godot_path), "returncode": result.returncode},
            )

        return GodotGetVersionResponse(version=version, path=str(godot_path))

    async def godot_list_projects(self, request: GodotListProjectsRequest) -> GodotListProjectsResponse:
        projects = list_projects(request.root_path)
        return GodotListProjectsResponse(projects=projects)

    async def godot_launch_editor(self, request: GodotLaunchEditorRequest) -> GodotLaunchEditorResponse:
        godot_path = discover_godot_executable()
        project_path = ensure_project_directory(request.project_path)
        session = await self.process_registry.create_session(
            godot_path=godot_path,
            project_path=project_path,
            mode="editor",
            headless=request.headless,
        )
        return GodotLaunchEditorResponse(session_id=session.session_id, pid=session.pid, status=session.status)

    async def godot_run_project(self, request: GodotRunProjectRequest) -> GodotRunProjectResponse:
        godot_path = discover_godot_executable()
        project_path = ensure_project_directory(request.project_path)
        session = await self.process_registry.create_session(
            godot_path=godot_path,
            project_path=project_path,
            mode="run",
            debug=request.debug,
            scene_override=request.scene_override,
        )
        return GodotRunProjectResponse(session_id=session.session_id, pid=session.pid, status=session.status)

    async def godot_stop_execution(self, request: GodotStopExecutionRequest) -> GodotStopExecutionResponse:
        stopped, exit_code = await self.process_registry.stop_session(request.session_id)
        return GodotStopExecutionResponse(stopped=stopped, exit_code=exit_code)

    async def godot_get_debug_output(self, request: GodotGetDebugOutputRequest) -> GodotGetDebugOutputResponse:
        entries, next_cursor = self.process_registry.get_output(
            session_id=request.session_id,
            limit=request.limit,
            cursor=request.cursor,
        )
        return GodotGetDebugOutputResponse(
            entries=[
                {
                    "cursor": item.cursor,
                    "timestamp": item.timestamp,
                    "stream": item.stream,
                    "message": item.message,
                }
                for item in entries
            ],
            next_cursor=next_cursor,
        )

    async def godot_analyze_project(self, request: GodotAnalyzeProjectRequest) -> GodotAnalyzeProjectResponse:
        return analyze_project(request.project_path)


def parse_arguments(model: type[BaseModel], arguments: dict[str, Any] | None) -> BaseModel:
    """Validate tool arguments and raise MCPError on validation failure."""
    payload = arguments or {}
    try:
        return model.model_validate(payload)
    except ValidationError as exc:
        raise MCPError(
            code="VALIDATION_ERROR",
            message="Invalid tool arguments.",
            details={"errors": exc.errors()},
        ) from exc

