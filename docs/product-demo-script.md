# Product Demo Script

Use this as a live 5-7 minute walkthrough.

## Demo Goal
Show that Mistral Vibe can orchestrate real Godot development tasks end-to-end through MCP tools:
1. understand a project,
2. change it,
3. run it,
4. see output,
5. interact with rendered content.

## Setup
1. Start MCP server:
```powershell
python -m mcp_server
```
2. Ensure Godot addon bridge is enabled in the target project.
3. Confirm token + URL are set:
   - `GODOT_BRIDGE_URL=http://127.0.0.1:19110`
   - `GODOT_BRIDGE_TOKEN=<your-token>`

## Narrative
"This project turns Godot into an agent-operable environment for Mistral Vibe. We expose structured MCP tools so automation can analyze projects, edit scenes, run/debug, capture renders, and interact with scenes programmatically."

## Live Flow (tool calls)
1. **Project understanding**
   - `godot_list_projects`
   - `godot_analyze_project`
2. **Scene creation/editing**
   - `scene_create`
   - `scene_add_node`
   - `scene_load_sprite`
   - `scene_save`
3. **Run and debug**
   - `godot_run_project`
   - `godot_get_debug_output`
4. **Rendered visibility + interaction**
   - `render_capture`
   - `render_interact`
   - `render_capture` again
5. **UID maintenance**
   - `uid_get`
   - `uid_refresh_references`

## Fallback Plan
1. Show `python -m pytest -q`.
2. Show `python -m leader_verify.smoke_stdio --json`.
3. Show captured render artifacts and tool responses from a prior run.

