# godot-mcp

https://github.com/user-attachments/assets/3b52def9-4663-4804-bb32-c7511511a422

MCP server that lets AI agents automate the Godot 4 game engine — create scenes, run projects, capture renders, and send input, all through the [Model Context Protocol](https://modelcontextprotocol.io/).

## Features

- **16 MCP tools** covering project control, scene editing, rendering, and interaction
- **Works with any MCP client** — Claude Code, Cursor, Windsurf, custom agents, etc.
- **Godot 4.4+** support via a lightweight GDScript addon bridge
- **Localhost-only** with token auth — no network exposure

## Agent Setup

If you're an AI agent (or configuring one), see **[SETUP_AGENT.md](SETUP_AGENT.md)** for machine-readable setup instructions with all env vars, tool signatures, and troubleshooting.

## Quick Start

### 1. Install

```bash
pip install pydantic
```

### 2. Set up the Godot bridge addon

1. Copy `godot_addon/mistral_mcp_bridge` into your Godot project as `addons/mistral_mcp_bridge`.
2. Enable the plugin in **Project > Project Settings > Plugins**.
3. Set a bridge token in project settings under `mistral_mcp/bridge_token`.

### 3. Run the MCP server

```bash
# Optional: point to your Godot executable
export GODOT_PATH="/path/to/godot"
export GODOT_BRIDGE_TOKEN="your-token"

python -m mcp_server
```

The server communicates over stdio (JSON-RPC with Content-Length framing).

### 4. Connect your MCP client

Add to your client's MCP config (e.g. `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "godot": {
      "command": "python",
      "args": ["-m", "mcp_server"],
      "cwd": "/path/to/this/repo"
    }
  }
}
```

## Tools

### Project & Process Control

| Tool | Description |
|------|-------------|
| `godot_get_version` | Get installed Godot version and executable path |
| `godot_list_projects` | Discover Godot projects recursively under a directory |
| `godot_launch_editor` | Launch the Godot editor for a project |
| `godot_run_project` | Run a project in game mode |
| `godot_stop_execution` | Stop a running Godot process |
| `godot_get_debug_output` | Read stdout/stderr with cursor-based pagination |
| `godot_analyze_project` | Static analysis of scenes, scripts, resources, autoloads |

### Scene Editing

| Tool | Description |
|------|-------------|
| `scene_create` | Create a new scene with a specified root node type |
| `scene_add_node` | Add a child node to an existing scene |
| `scene_load_sprite` | Load a texture into a Sprite2D node |
| `scene_export_mesh_library` | Export a MeshLibrary for 3D tilesets |
| `scene_save` | Save a scene or create an inherited variant |

### Resources

| Tool | Description |
|------|-------------|
| `uid_get` | Get the Godot UID for a resource |
| `uid_refresh_references` | Update UID references across the project |

### Rendering & Interaction

| Tool | Description |
|------|-------------|
| `render_capture` | Screenshot the editor or running game |
| `render_interact` | Send mouse clicks, key presses, or camera controls |

## Examples

```json
// Create a 3D scene
{
  "tool": "scene_create",
  "arguments": {
    "project_path": "C:/Projects/MyGame",
    "scene_path": "scenes/level_01.tscn",
    "root_node_type": "Node3D"
  }
}
```

```json
// Capture a screenshot of the running game
{
  "tool": "render_capture",
  "arguments": {
    "project_path": "C:/Projects/MyGame",
    "mode": "running",
    "width": 1280,
    "height": 720
  }
}
```

```json
// Click in the game window
{
  "tool": "render_interact",
  "arguments": {
    "project_path": "C:/Projects/MyGame",
    "mode": "mouse_click",
    "payload": { "x": 640, "y": 360, "button": 1 }
  }
}
```

## Architecture

```
MCP Client  <--stdio-->  mcp_server (Python)  <--HTTP-->  Godot Bridge Addon (GDScript)
                                                           127.0.0.1:19110 + Bearer token
```

- **`mcp_server/`** — Python MCP server handling tool dispatch and validation (Pydantic schemas)
- **`godot_addon/mistral_mcp_bridge/`** — GDScript @tool plugin running an HTTP server inside the Godot editor

## Testing

```bash
# Unit tests
python -m pytest -q

# Integration tests (requires Godot 4.4+)
ENABLE_GODOT_INTEGRATION=1 GODOT_PATH="/path/to/godot" python -m pytest -q tests_integration
```

## Requirements

- Python 3.11+
- Godot 4.4+
- `pydantic`

## License

See [LICENSE](LICENSE) for details.
