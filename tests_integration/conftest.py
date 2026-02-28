from __future__ import annotations

import asyncio
import os
import socket
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio

from mcp_server.bridge_client import GodotBridgeClient
from mcp_server.errors import MCPError
from mcp_server.godot_discovery import discover_godot_executable
from mcp_server.models import GodotLaunchEditorRequest, GodotStopExecutionRequest
from mcp_server.tools import GodotToolService


REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_PROJECT = REPO_ROOT / "examples" / "minimal_godot_project"
ADDON_SOURCE = REPO_ROOT / "godot_addon" / "mistral_mcp_bridge"
BRIDGE_TOKEN = "integration-token"


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    del config
    for item in items:
        item.add_marker(pytest.mark.godot_integration)


@pytest.fixture(scope="session", autouse=True)
def _require_opt_in() -> None:
    if os.getenv("ENABLE_GODOT_INTEGRATION") != "1":
        pytest.skip("Set ENABLE_GODOT_INTEGRATION=1 to run Godot integration tests.", allow_module_level=True)


@pytest.fixture(scope="session")
def godot_path() -> Path:
    try:
        resolved = discover_godot_executable()
    except MCPError as exc:
        pytest.fail(
            "ENABLE_GODOT_INTEGRATION=1 was set, but Godot was not found. "
            "Set GODOT_PATH to a Godot 4.4+ executable. "
            f"Details: {exc.to_dict()}"
        )
    return resolved


@pytest.fixture(scope="session")
def integration_project(tmp_path_factory: pytest.TempPathFactory, bridge_port: int) -> Path:
    temp_root = tmp_path_factory.mktemp("godot_it_project")
    project_path = temp_root / "project"
    shutil.copytree(EXAMPLE_PROJECT, project_path)
    addon_dest = project_path / "addons" / "mistral_mcp_bridge"
    shutil.copytree(ADDON_SOURCE, addon_dest)
    project_file = project_path / "project.godot"
    content = project_file.read_text(encoding="utf-8")
    if "bridge_port=" in content:
        import re

        content = re.sub(r"bridge_port=\d+", f"bridge_port={bridge_port}", content)
    else:
        content += f"\n[mistral_mcp]\nbridge_port={bridge_port}\n"
    project_file.write_text(content, encoding="utf-8")
    return project_path


@dataclass(slots=True)
class ToolHarness:
    service: GodotToolService
    bridge_url: str
    sessions: list[str] = field(default_factory=list)

    async def launch_editor(self, project_path: str) -> Any:
        response = await self.service.godot_launch_editor(GodotLaunchEditorRequest(project_path=project_path, headless=False))
        self.sessions.append(response.session_id)
        return response

    async def stop_all(self) -> None:
        for session_id in list(reversed(self.sessions)):
            try:
                await self.service.godot_stop_execution(GodotStopExecutionRequest(session_id=session_id))
            except Exception:
                pass
        self.sessions.clear()

    async def wait_for_bridge(self, timeout_s: float = 30.0) -> None:
        await wait_for_bridge(self.bridge_url, timeout_s=timeout_s)


def _set_env(godot_executable: Path, bridge_url: str) -> dict[str, str | None]:
    previous = {
        "GODOT_PATH": os.getenv("GODOT_PATH"),
        "GODOT_BRIDGE_URL": os.getenv("GODOT_BRIDGE_URL"),
        "GODOT_BRIDGE_TOKEN": os.getenv("GODOT_BRIDGE_TOKEN"),
    }
    os.environ["GODOT_PATH"] = str(godot_executable)
    os.environ["GODOT_BRIDGE_URL"] = bridge_url
    os.environ["GODOT_BRIDGE_TOKEN"] = BRIDGE_TOKEN
    return previous


def _restore_env(previous: dict[str, str | None]) -> None:
    for key, value in previous.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def _pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture(scope="session")
def bridge_port() -> int:
    return _pick_free_port()


@pytest.fixture(scope="session")
def bridge_url(bridge_port: int) -> str:
    return f"http://127.0.0.1:{bridge_port}"


async def wait_for_bridge(bridge_url: str, timeout_s: float = 30.0) -> None:
    client = GodotBridgeClient(base_url=bridge_url, token=BRIDGE_TOKEN)
    deadline = time.time() + timeout_s
    last_error: Exception | str | None = None
    while time.time() < deadline:
        try:
            response = await asyncio.to_thread(client.health)
            if response.get("ok") is True:
                return
            last_error = f"health response not ready: {response}"
        except Exception as exc:  # pragma: no cover - runtime-specific
            last_error = repr(exc)
        await asyncio.sleep(0.5)
    pytest.fail(f"Bridge did not become healthy within {timeout_s}s. Last error: {last_error}")


@pytest_asyncio.fixture
async def harness(godot_path: Path, bridge_url: str) -> ToolHarness:
    previous = _set_env(godot_path, bridge_url)
    service = GodotToolService()
    session_harness = ToolHarness(service=service, bridge_url=bridge_url)
    try:
        yield session_harness
    finally:
        await session_harness.stop_all()
        _restore_env(previous)
