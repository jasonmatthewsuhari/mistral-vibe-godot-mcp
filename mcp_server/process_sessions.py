from __future__ import annotations

import os
import shutil
import subprocess
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from mcp_server.errors import make_error


@dataclass(slots=True)
class SessionRecord:
    session_id: str
    pid: int
    mode: str
    project_path: str
    started_at: str
    status: str = "running"
    exit_code: int | None = None
    process: subprocess.Popen[str] | None = field(default=None, repr=False)


class GodotLocator:
    def __init__(
        self,
        env: dict[str, str] | None = None,
        which: Callable[[str], str | None] | None = None,
        common_paths: list[str] | None = None,
    ) -> None:
        self.env = env or dict(os.environ)
        self.which = which or shutil.which
        self.common_paths = common_paths or [
            r"C:\Program Files\Godot\Godot_v4.4-stable_win64.exe",
            r"C:\Program Files\Godot Engine\godot.exe",
            r"C:\Program Files\Godot Engine\Godot_v4.4-stable_win64.exe",
        ]

    def find(self, explicit_path: str | None = None) -> str:
        if explicit_path:
            path = Path(explicit_path)
            if path.exists():
                return str(path)
            raise make_error("not_found", "Configured Godot binary does not exist", {"path": explicit_path})

        env_path = self.env.get("GODOT_PATH")
        if env_path:
            path = Path(env_path)
            if path.exists():
                return str(path)
            raise make_error("not_found", "GODOT_PATH points to a missing file", {"path": env_path})

        on_path = self.which("godot")
        if on_path:
            return on_path

        for candidate in self.common_paths:
            if Path(candidate).exists():
                return candidate

        raise make_error("runtime_dependency_error", "Unable to find Godot executable")


class SessionRegistry:
    def __init__(self) -> None:
        self._sessions: dict[str, SessionRecord] = {}

    def create(self, pid: int, mode: str, project_path: str, process: subprocess.Popen[str] | None = None) -> SessionRecord:
        record = SessionRecord(
            session_id=str(uuid.uuid4()),
            pid=pid,
            mode=mode,
            project_path=project_path,
            process=process,
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        self._sessions[record.session_id] = record
        return record

    def get(self, session_id: str) -> SessionRecord:
        if session_id not in self._sessions:
            raise make_error("not_found", "Session not found", {"session_id": session_id})
        return self._sessions[session_id]

    def stop(self, session_id: str) -> SessionRecord:
        record = self.get(session_id)
        proc = record.process
        if proc and proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=5)
        record.exit_code = proc.returncode if proc else 0
        record.status = "stopped"
        return record


def validate_project_path(project_path: str) -> str:
    project = Path(project_path).expanduser().resolve()
    if not project.exists() or not project.is_dir():
        raise make_error("not_found", "Project path does not exist", {"project_path": str(project)})
    project_file = project / "project.godot"
    if not project_file.exists():
        raise make_error("not_found", "project.godot not found", {"project_path": str(project)})
    return str(project)


class GodotProcessManager:
    def __init__(
        self,
        locator: GodotLocator | None = None,
        registry: SessionRegistry | None = None,
        popen: Callable[..., subprocess.Popen[str]] | None = None,
    ) -> None:
        self.locator = locator or GodotLocator()
        self.registry = registry or SessionRegistry()
        self._popen = popen or subprocess.Popen

    def launch_editor(self, project_path: str, headless: bool = False) -> SessionRecord:
        validated_path = validate_project_path(project_path)
        godot_bin = self.locator.find()
        cmd = [godot_bin, "--path", validated_path, "--editor"]
        if headless:
            cmd.append("--headless")
        process = self._popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return self.registry.create(pid=process.pid, mode="editor", project_path=validated_path, process=process)

    def run_project(self, project_path: str, debug: bool = True, scene_override: str | None = None) -> SessionRecord:
        validated_path = validate_project_path(project_path)
        godot_bin = self.locator.find()
        cmd = [godot_bin, "--path", validated_path]
        if debug:
            cmd.append("--debug")
        if scene_override:
            cmd.extend(["--main-pack", scene_override])
        process = self._popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return self.registry.create(pid=process.pid, mode="run", project_path=validated_path, process=process)
