from __future__ import annotations

from typing import Any

from mcp_server.bridge_client import GodotBridgeClient


def test_bridge_client_uses_bearer_token_header() -> None:
    captured: dict[str, Any] = {}

    def transport(**kwargs: Any) -> dict[str, Any]:
        captured.update(kwargs)
        return {"ok": True}

    client = GodotBridgeClient(base_url="http://127.0.0.1:19110", token="secret", transport=transport)
    response = client.health()

    assert response["ok"] is True
    assert captured["method"] == "GET"
    assert captured["url"] == "http://127.0.0.1:19110/health"
    assert captured["headers"]["Authorization"] == "Bearer secret"


def test_bridge_client_route_contract() -> None:
    calls: list[tuple[str, str]] = []

    def transport(**kwargs: Any) -> dict[str, Any]:
        calls.append((kwargs["method"], kwargs["url"]))
        return {"ok": True}

    client = GodotBridgeClient(base_url="http://127.0.0.1:19110", token="secret", transport=transport)
    client.scene_create({})
    client.scene_add_node({})
    client.scene_load_sprite({})
    client.scene_export_mesh_library({})
    client.scene_save({})
    client.uid_get({})
    client.uid_refresh({})
    client.render_capture({})
    client.render_interact({})

    assert calls == [
        ("POST", "http://127.0.0.1:19110/scene/create"),
        ("POST", "http://127.0.0.1:19110/scene/add_node"),
        ("POST", "http://127.0.0.1:19110/scene/load_sprite"),
        ("POST", "http://127.0.0.1:19110/scene/export_mesh_library"),
        ("POST", "http://127.0.0.1:19110/scene/save"),
        ("POST", "http://127.0.0.1:19110/uid/get"),
        ("POST", "http://127.0.0.1:19110/uid/refresh"),
        ("POST", "http://127.0.0.1:19110/render/capture"),
        ("POST", "http://127.0.0.1:19110/render/interact"),
    ]


def test_bridge_client_stub_response_when_transport_missing() -> None:
    calls: list[tuple[str, str]] = []

    def transport(**kwargs: Any) -> dict[str, Any]:
        calls.append((kwargs["method"], kwargs["url"]))
        return {"ok": True}

    client = GodotBridgeClient(token="secret", transport=transport)
    response = client.uid_refresh_references({"paths": ["res://a.tres"]})
    assert response["ok"] is True
    assert calls == [("POST", "http://127.0.0.1:19110/uid/refresh")]
