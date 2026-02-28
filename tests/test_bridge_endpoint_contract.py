from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PRIMARY_BRIDGE = REPO_ROOT / "godot_addon" / "mistral_mcp_bridge" / "bridge_entry.gd"
ADDON_BRIDGE = REPO_ROOT / "godot_addon" / "addons" / "mistral_mcp_bridge" / "bridge_entry.gd"


def test_bridge_endpoint_route_matrix_is_present() -> None:
    source = PRIMARY_BRIDGE.read_text(encoding="utf-8")
    expected_routes = [
        "/health",
        "/scene/create",
        "/scene/add_node",
        "/scene/load_sprite",
        "/scene/export_mesh_library",
        "/scene/save",
        "/uid/get",
        "/uid/refresh",
        "/render/capture",
        "/render/interact",
    ]
    for route in expected_routes:
        assert route in source


def test_bridge_security_and_failure_codes_are_present() -> None:
    source = PRIMARY_BRIDGE.read_text(encoding="utf-8")
    assert 'bind_host != "127.0.0.1"' in source
    assert 'auth_header.begins_with("Bearer ")' in source
    assert "Missing or invalid bearer token" in source

    # Required failure-path coverage for endpoint behavior.
    assert "scene_not_found" in source
    assert "node_not_found" in source
    assert "resource_not_found" in source


def test_bridge_files_are_kept_in_sync() -> None:
    assert PRIMARY_BRIDGE.read_text(encoding="utf-8") == ADDON_BRIDGE.read_text(encoding="utf-8")

