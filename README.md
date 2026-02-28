# mistral-vibe-godot-mcp

MCP server for Godot engine automation designed for Mistral Vibe workflows.  

https://github.com/user-attachments/assets/3b52def9-4663-4804-bb32-c7511511a422

## Mistral Vibe Positioning
This project is explicitly designed as a **Mistral Vibe-native** developer tool:
- Terminal-first MCP workflow for coding/automation loops.
- Agent-compatible tool surface for delegation and subagent orchestration.
- Safe, explicit local-tool execution (Godot process control + localhost bridge auth).
- Practical game-dev automation use case with structured MCP tooling.

Reference context:
- Mistral Vibe product page: https://mistral.ai/products/vibe
- Mistral Vibe docs: https://docs.mistral.ai/mistral-vibe/introduction
- Agents & skills in Vibe: https://docs.mistral.ai/mistral-vibe/agents-skills

## Run (MCP stdio)
1. Install Python 3.11+ and `pydantic`.
2. Optional: set `GODOT_PATH` to your Godot executable (Windows example: `C:\Program Files\Godot\Godot_v4.4-stable_win64.exe`).
3. Start the MCP server over stdio:

```powershell
python -m mcp_server
```

## Developer Testing
- Test runner: `pytest`
- Run from repo root:
  - `python -m pytest -q`
- Scope of current tests:
  - Tool payload/schema validation (`tests/test_tool_contracts.py`)
  - Project discovery (`tests/test_project_discovery.py`)
  - Debug output cursor and ring buffer behavior (`tests/test_debug_buffer.py`)
  - Process/session behavior and error paths for missing project/missing Godot (`tests/test_process_sessions.py`)
  - Opt-in Godot runtime smoke tests (`tests_integration/`)

## Integration Testing (Opt-In)
These tests are skipped by default and only run when explicitly enabled.

1. Set required environment variables:
   - `ENABLE_GODOT_INTEGRATION=1`
   - `GODOT_PATH=<absolute path to Godot 4.4+ executable>` (preferred for deterministic runs)
   - Optional:
     - `GODOT_BRIDGE_URL=http://127.0.0.1:19110`
     - `GODOT_BRIDGE_TOKEN=integration-token`
2. Run integration tests:
   - `python -m pytest -q tests_integration -m godot_integration`
3. Run full suite (unit + integration):
   - `python -m pytest -q`

Troubleshooting:
- Godot path issues:
  - If enabled and Godot is missing, tests fail fast with clear instructions.
  - Set `GODOT_PATH` directly to avoid discovery ambiguity.
- Bridge token mismatch:
  - Integration fixture project sets `mistral_mcp/bridge_token=integration-token`.
  - Ensure `GODOT_BRIDGE_TOKEN` matches this value.
- Port conflict (`127.0.0.1:19110`):
  - Stop other Godot/editor bridge instances before running integration tests.
  - If needed, update both bridge URL env var and addon bind settings consistently.

## Godot Bridge Setup (Addon)
1. Copy `godot_addon/mistral_mcp_bridge` into your Godot project as `addons/mistral_mcp_bridge`.
2. In Godot, enable plugin `Mistral MCP Bridge` under `Project > Project Settings > Plugins`.
3. Set bridge token in project settings key `mistral_mcp/bridge_token`.
4. The bridge binds only to `127.0.0.1:19110` and requires:
   - `Authorization: Bearer <token>`

## Why This Fits Mistral Vibe
- Works naturally with Vibe's terminal-native coding loop and tool execution model.
- Exposes a broad, structured MCP tool catalog for autonomous coding tasks.
- Supports delegated workflows (subagents can call project analysis, scene ops, and render tools in parallel).
- Keeps local safety boundaries explicit (localhost bridge + token + project path validation).

## Product Demo
- Walkthrough: [docs/product-demo-script.md](C:\Users\Jason\Documents\GitHub\mistral-vibe-godot-mcp\docs\product-demo-script.md)
- Demonstrates end-to-end orchestration across analysis, scene editing, runtime control, render capture, and interaction.

## Tool Examples
Scene create:
```json
{
  "tool": "scene_create",
  "arguments": {
    "project_path": "C:/Projects/MyGame",
    "scene_path": "scenes/level_01.tscn",
    "root_node_type": "Node3D"
  }
}
```

UID get:
```json
{
  "tool": "uid_get",
  "arguments": {
    "project_path": "C:/Projects/MyGame",
    "resource_path": "res://art/hero.png"
  }
}
```

Render capture:
```json
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

Render interact (mouse click):
```json
{
  "tool": "render_interact",
  "arguments": {
    "project_path": "C:/Projects/MyGame",
    "mode": "mouse_click",
    "payload": {
      "x": 640,
      "y": 360,
      "button": 1
    }
  }
}
```
