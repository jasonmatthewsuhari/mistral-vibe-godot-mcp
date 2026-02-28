from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from mcp_server.models import (
    GodotGetDebugOutputRequest,
    GodotGetVersionRequest,
    GodotRunProjectRequest,
    GodotStopExecutionRequest,
    RenderCaptureRequest,
    RenderInteractRequest,
    SceneAddNodeRequest,
    SceneCreateRequest,
    SceneLoadSpriteRequest,
    SceneSaveRequest,
    UidGetRequest,
    UidRefreshReferencesRequest,
)


@pytest.mark.asyncio
async def test_godot_get_version(harness) -> None:
    response = await harness.service.godot_get_version(GodotGetVersionRequest())
    assert response.version
    assert Path(response.path).exists()


@pytest.mark.asyncio
async def test_launch_editor_and_stop(harness, integration_project: Path) -> None:
    launch = await harness.launch_editor(str(integration_project))
    assert launch.status == "running"
    assert launch.pid > 0

    stop = await harness.service.godot_stop_execution(GodotStopExecutionRequest(session_id=launch.session_id))
    assert stop.stopped is True

    # Prevent double-stop in finalizer.
    harness.sessions.remove(launch.session_id)


@pytest.mark.asyncio
async def test_run_project_and_get_debug_output(harness, integration_project: Path) -> None:
    run = await harness.service.godot_run_project(GodotRunProjectRequest(project_path=str(integration_project), debug=True))
    harness.sessions.append(run.session_id)
    await asyncio.sleep(1.5)

    debug_output = await harness.service.godot_get_debug_output(
        GodotGetDebugOutputRequest(session_id=run.session_id, limit=20, cursor=None)
    )
    assert len(debug_output.entries) >= 1
    assert any("Started command:" in entry.message for entry in debug_output.entries)

    stop = await harness.service.godot_stop_execution(GodotStopExecutionRequest(session_id=run.session_id))
    assert stop.stopped is True
    harness.sessions.remove(run.session_id)


@pytest.mark.asyncio
async def test_scene_uid_render_end_to_end(harness, integration_project: Path, tmp_path: Path) -> None:
    del tmp_path
    launch = await harness.service.godot_run_project(
        GodotRunProjectRequest(project_path=str(integration_project), debug=True)
    )
    harness.sessions.append(launch.session_id)
    await harness.wait_for_bridge(timeout_s=45.0)

    created = await harness.service.scene_create(
        SceneCreateRequest(
            project_path=str(integration_project),
            scene_path="res://scenes/generated_scene.tscn",
            root_node_type="Node2D",
        )
    )
    assert created.scene_path.endswith("generated_scene.tscn")

    added = await harness.service.scene_add_node(
        SceneAddNodeRequest(
            project_path=str(integration_project),
            scene_path=created.scene_path,
            parent_node_path=".",
            node_type="Sprite2D",
            node_name="GeneratedSprite",
            properties=None,
        )
    )
    assert "GeneratedSprite" in added.node_path

    sprite = await harness.service.scene_load_sprite(
        SceneLoadSpriteRequest(
            project_path=str(integration_project),
            scene_path=created.scene_path,
            sprite_node_path="GeneratedSprite",
            texture_path="res://assets/test_texture.png",
            import_if_needed=True,
        )
    )
    assert sprite.sprite_node_path == "GeneratedSprite"

    saved = await harness.service.scene_save(
        SceneSaveRequest(
            project_path=str(integration_project),
            scene_path=created.scene_path,
            variant_name="it",
            make_inherited=False,
        )
    )
    assert saved.saved_path.endswith("_it.tscn")

    uid = await harness.service.uid_get(
        UidGetRequest(
            project_path=str(integration_project),
            resource_path="res://assets/test_texture.png",
        )
    )
    assert uid.uid

    refreshed = await harness.service.uid_refresh_references(
        UidRefreshReferencesRequest(
            project_path=str(integration_project),
            paths=["res://assets/test_texture.png", created.scene_path],
        )
    )
    assert refreshed.updated_count >= 1

    capture = await harness.service.render_capture(
        RenderCaptureRequest(
            project_path=str(integration_project),
            mode="running",
            width=320,
            height=180,
        )
    )
    image_path = Path(capture.image_path)
    assert image_path.exists()
    assert capture.width == 320
    assert capture.height == 180

    interaction = await harness.service.render_interact(
        RenderInteractRequest(
            project_path=str(integration_project),
            mode="mouse_click",
            payload={"x": 80, "y": 40, "button": 1},
        )
    )
    assert interaction.ok is True

    stop = await harness.service.godot_stop_execution(GodotStopExecutionRequest(session_id=launch.session_id))
    assert stop.stopped is True
    harness.sessions.remove(launch.session_id)
