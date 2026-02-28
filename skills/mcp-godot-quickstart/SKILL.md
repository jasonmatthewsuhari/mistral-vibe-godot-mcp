# MCP Godot Quickstart

Use this skill to quickly run and use the Godot MCP server in local workflows.

## When to use
- You want to start the MCP server and call tools immediately.
- You need the shortest path to verify Godot integration works.

## Prerequisites
- Python available on PATH.
- Godot installed (recommended: set `GODOT_PATH`).
- Optional bridge env:
  - `GODOT_BRIDGE_URL` (default `http://127.0.0.1:19110`)
  - `GODOT_BRIDGE_TOKEN`

## Start server
```powershell
python -m mcp_server
```

## Fast health checks
```powershell
python -m leader_verify.smoke_stdio
python scripts/validate_tool_name_parity.py --json
python -m pytest -q
```

## Core MCP tools
- `godot_get_version`
- `godot_list_projects`
- `godot_launch_editor`
- `godot_run_project`
- `godot_stop_execution`
- `godot_get_debug_output`
- `godot_analyze_project`

## Scene / UID / Render tools
- `scene_create`, `scene_add_node`, `scene_load_sprite`, `scene_export_mesh_library`, `scene_save`
- `uid_get`, `uid_refresh_references`
- `render_capture`, `render_interact`

## Typical first workflow
1. `godot_list_projects`
2. `godot_analyze_project`
3. `scene_create` + `scene_add_node`
4. `godot_run_project`
5. `godot_get_debug_output`
6. `render_capture`

## Troubleshooting
- Run `scripts/release_diagnostics.ps1` for environment/tool visibility.
- See `TROUBLESHOOTING.md` for bridge token, path, and port issues.
