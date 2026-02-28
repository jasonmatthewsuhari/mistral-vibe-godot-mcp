from __future__ import annotations

from typing import Any

from mcp_server.bridge_client import GodotBridgeClient


def _fake_bridge_transport(**kwargs: Any) -> dict[str, Any]:
    headers = kwargs.get("headers", {})
    payload = kwargs.get("payload") or {}
    auth = headers.get("Authorization", "")
    if auth != "Bearer valid-token":
        return {"ok": False, "error": {"code": "unauthorized", "message": "Missing or invalid bearer token"}}

    url = kwargs.get("url", "")
    if url.endswith("/scene/add_node") and payload.get("parent_node_path") == "Missing":
        return {"ok": False, "error": {"code": "node_not_found", "message": "Parent node path not found"}}
    if url.endswith("/scene/load_sprite") and payload.get("texture_path") == "res://missing.png":
        return {"ok": False, "error": {"code": "resource_not_found", "message": "Texture resource not found"}}
    if url.endswith("/scene/save") and payload.get("scene_path") == "res://missing_scene.tscn":
        return {"ok": False, "error": {"code": "scene_not_found", "message": "Scene file not found"}}
    return {"ok": True}


def test_bad_token_failure_path() -> None:
    client = GodotBridgeClient(token="bad-token", transport=_fake_bridge_transport)
    response = client.health()
    assert response["ok"] is False
    assert response["error"]["code"] == "unauthorized"


def test_missing_node_failure_path() -> None:
    client = GodotBridgeClient(token="valid-token", transport=_fake_bridge_transport)
    response = client.scene_add_node({"parent_node_path": "Missing"})
    assert response["ok"] is False
    assert response["error"]["code"] == "node_not_found"


def test_missing_resource_failure_path() -> None:
    client = GodotBridgeClient(token="valid-token", transport=_fake_bridge_transport)
    response = client.scene_load_sprite({"texture_path": "res://missing.png"})
    assert response["ok"] is False
    assert response["error"]["code"] == "resource_not_found"


def test_missing_scene_failure_path() -> None:
    client = GodotBridgeClient(token="valid-token", transport=_fake_bridge_transport)
    response = client.scene_save({"scene_path": "res://missing_scene.tscn"})
    assert response["ok"] is False
    assert response["error"]["code"] == "scene_not_found"

