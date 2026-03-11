# Godot MCP — Agent Setup Guide

This file is for AI agents to read and execute. It contains everything needed to set up the Godot MCP server for a project.

## Prerequisites

- Python 3.11+
- Godot 4.4+
- `pydantic` installed (`pip install pydantic`)

## Step 1: Locate the Godot MCP repo

The MCP server source lives in this repository. Note the absolute path — you will need it for the MCP client config.

```
GODOT_MCP_REPO="/path/to/godot-mcp"
```

## Step 2: Install the Godot bridge addon

Copy the addon into the target Godot project:

```bash
cp -r "$GODOT_MCP_REPO/godot_addon/mistral_mcp_bridge" "<GODOT_PROJECT>/addons/mistral_mcp_bridge"
```

Then enable the plugin by adding to `<GODOT_PROJECT>/project.godot`:

```ini
[editor_plugins]
enabled=PackedStringArray("res://addons/mistral_mcp_bridge/plugin.cfg")
```

If the `[editor_plugins]` section already exists, append `"res://addons/mistral_mcp_bridge/plugin.cfg"` to the existing `PackedStringArray`.

## Step 3: Set the bridge token

Choose a token string (any non-empty value). Add to `<GODOT_PROJECT>/project.godot`:

```ini
[mistral_mcp]
bridge_token="<TOKEN>"
```

This token authenticates HTTP requests between the MCP server and the Godot bridge. It must match on both sides.

## Step 4: Set environment variables

```bash
# Required: must match the token in project.godot
export GODOT_BRIDGE_TOKEN="<TOKEN>"

# Optional: path to Godot executable (auto-discovered if on PATH)
export GODOT_PATH="/path/to/godot"

# Optional: override bridge URL (default: http://127.0.0.1:19110)
# export GODOT_BRIDGE_URL="http://127.0.0.1:19110"

# Optional: HTTP timeout in seconds (default: 5.0)
# export GODOT_BRIDGE_TIMEOUT_S="5.0"
```

## Step 5: Register the MCP server with your client

Add to your MCP client config (e.g. `claude_desktop_config.json`, `.cursor/mcp.json`, etc.):

```json
{
  "mcpServers": {
    "godot": {
      "command": "python",
      "args": ["-m", "mcp_server"],
      "cwd": "<GODOT_MCP_REPO>",
      "env": {
        "GODOT_BRIDGE_TOKEN": "<TOKEN>",
        "GODOT_PATH": "/path/to/godot"
      }
    }
  }
}
```

Replace `<GODOT_MCP_REPO>` with the absolute path to this repository, `<TOKEN>` with your chosen token, and `GODOT_PATH` with your Godot executable path.

## Step 6: Verify

1. Open the Godot project in the editor (the bridge starts automatically when the plugin loads).
2. Start the MCP server: `python -m mcp_server` (or let your MCP client start it).
3. Call `godot_get_version` — if it returns the Godot version and path, the server is working.
4. Call `render_capture` — if it returns a screenshot, the bridge is connected and authenticated.

## Available Tools (16)

### Project & Process Control

| Tool | Required Args | Description |
|------|---------------|-------------|
| `godot_get_version` | — | Get installed Godot version and executable path |
| `godot_list_projects` | `root_path` | Discover Godot projects recursively |
| `godot_launch_editor` | `project_path` | Launch the Godot editor |
| `godot_run_project` | `project_path` | Run a project in game mode |
| `godot_stop_execution` | — | Stop a running Godot process |
| `godot_get_debug_output` | — | Read stdout/stderr with cursor pagination |
| `godot_analyze_project` | `project_path` | Static analysis of project structure |

### Scene Editing

| Tool | Required Args | Description |
|------|---------------|-------------|
| `scene_create` | `project_path`, `scene_path`, `root_node_type` | Create a new scene |
| `scene_add_node` | `project_path`, `scene_path`, `parent_node_path`, `node_name`, `node_type` | Add a node to a scene |
| `scene_load_sprite` | `project_path`, `scene_path`, `sprite_node_path`, `texture_path` | Load a texture into a Sprite2D |
| `scene_export_mesh_library` | `project_path`, `source_scene_path`, `mesh_library_path` | Export a MeshLibrary |
| `scene_save` | `project_path`, `scene_path` | Save a scene |

### Resources

| Tool | Required Args | Description |
|------|---------------|-------------|
| `uid_get` | `project_path`, `resource_path` | Get a resource's UID |
| `uid_refresh_references` | `project_path` | Refresh UID references project-wide |

### Rendering & Interaction

| Tool | Required Args | Description |
|------|---------------|-------------|
| `render_capture` | `project_path` | Screenshot the editor or running game |
| `render_interact` | `project_path`, `mode`, `payload` | Send mouse/keyboard/camera input |

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `GODOT_NOT_FOUND` | Godot not on PATH and `GODOT_PATH` not set | Set `GODOT_PATH` to the Godot executable |
| `BRIDGE_UNREACHABLE` | Godot editor not running or plugin not enabled | Open the project in Godot editor with the plugin enabled |
| `401 Unauthorized` | Token mismatch | Ensure `GODOT_BRIDGE_TOKEN` env var matches `bridge_token` in `project.godot` |
| Port 19110 in use | Another process on that port | Stop the conflicting process |

## Security Notes

- The bridge binds to `127.0.0.1` only — no remote access possible.
- Every request requires a `Bearer <token>` header.
- Use a unique token per project. Never commit tokens to version control.
