from pathlib import Path

import pytest

from mcp_server.errors import MCPError
from mcp_server.process_sessions import (
    GodotLocator,
    GodotProcessManager,
    SessionRegistry,
    validate_project_path,
)


class DummyPopen:
    _next_pid = 1000

    def __init__(self, cmd, **_kwargs):
        self.cmd = cmd
        self.pid = DummyPopen._next_pid
        DummyPopen._next_pid += 1
        self.returncode = None
        self._terminated = False

    def poll(self):
        return self.returncode

    def terminate(self):
        self._terminated = True
        self.returncode = 0

    def wait(self, timeout=5):
        del timeout
        if self.returncode is None:
            self.returncode = 0
        return self.returncode


def _create_project(tmp_path: Path, name: str = "demo") -> Path:
    project_path = tmp_path / name
    project_path.mkdir(parents=True, exist_ok=True)
    (project_path / "project.godot").write_text("[gd_project]\n", encoding="utf-8")
    return project_path


def test_validate_project_path_requires_project_file(tmp_path: Path) -> None:
    no_project_file = tmp_path / "missing_project_file"
    no_project_file.mkdir()
    with pytest.raises(MCPError) as exc:
        validate_project_path(str(no_project_file))
    assert exc.value.code == "not_found"


def test_missing_godot_binary_raises_dependency_error() -> None:
    locator = GodotLocator(env={}, which=lambda _name: None, common_paths=[])
    with pytest.raises(MCPError) as exc:
        locator.find()
    assert exc.value.code == "runtime_dependency_error"


def test_launch_and_stop_session(tmp_path: Path) -> None:
    project = _create_project(tmp_path)
    fake_godot = tmp_path / "godot.exe"
    fake_godot.write_text("", encoding="utf-8")
    manager = GodotProcessManager(
        locator=GodotLocator(env={"GODOT_PATH": str(fake_godot)}),
        registry=SessionRegistry(),
        popen=DummyPopen,
    )

    session = manager.launch_editor(str(project))
    assert session.mode == "editor"
    assert session.status == "running"

    stopped = manager.registry.stop(session.session_id)
    assert stopped.status == "stopped"
    assert stopped.exit_code == 0


def test_launch_editor_raises_on_missing_project(tmp_path: Path) -> None:
    fake_godot = tmp_path / "godot.exe"
    fake_godot.write_text("", encoding="utf-8")
    manager = GodotProcessManager(
        locator=GodotLocator(env={"GODOT_PATH": str(fake_godot)}),
        registry=SessionRegistry(),
        popen=DummyPopen,
    )
    with pytest.raises(MCPError) as exc:
        manager.launch_editor(str(tmp_path / "unknown_project"))
    assert exc.value.code == "not_found"
