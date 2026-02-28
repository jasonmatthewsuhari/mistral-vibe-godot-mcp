# mistral-vibe-godot-mcp
MCP server for Godot game engine built during the Mistral Worldwide Hackathon, because we like to take laziness to another level. Also hoping to get the Best Use of Mistral Vibe track :D

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
