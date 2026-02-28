from __future__ import annotations

import asyncio
import io
from pathlib import Path

import pytest

from mcp_server.process_registry import ProcessRegistry


class DummyPopen:
    def __init__(self, _args, **_kwargs):
        self.pid = 4321
        self.returncode = None
        self.stdout = io.StringIO("fallback-stdout\n")
        self.stderr = io.StringIO("")

    def terminate(self) -> None:
        self.returncode = 0

    def kill(self) -> None:
        self.returncode = -9

    def wait(self) -> int:
        if self.returncode is None:
            self.returncode = 0
        return self.returncode


@pytest.mark.asyncio
async def test_create_session_falls_back_to_popen_on_permission_error(monkeypatch, tmp_path: Path) -> None:
    async def fake_create_subprocess_exec(*_args, **_kwargs):
        raise PermissionError(5, "Access is denied")

    monkeypatch.setattr("mcp_server.process_registry.asyncio.create_subprocess_exec", fake_create_subprocess_exec)
    monkeypatch.setattr("mcp_server.process_registry.subprocess.Popen", DummyPopen)

    registry = ProcessRegistry()
    session = await registry.create_session(
        godot_path=tmp_path / "godot.exe",
        project_path=tmp_path,
        mode="run",
        debug=True,
    )

    assert session.pid == 4321
    assert session.status == "running"

    # Let background tasks flush buffered output.
    await asyncio.sleep(0.05)
    entries, _ = registry.get_output(session_id=session.session_id, limit=20, cursor=None)
    assert any("Started command:" in entry.message for entry in entries)
    assert any("fallback-stdout" in entry.message for entry in entries)
