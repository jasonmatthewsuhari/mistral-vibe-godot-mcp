# Subagent Verification Checklist

Use this checklist to verify incoming changes against `IMPLEMENTATION_PLAN.md`.

## 1) Core MCP Server (Python stdio)
- Server starts in stdio mode without crashing.
- Tool registration exists for each implemented tool.
- Tool input/output uses typed schemas (Pydantic or equivalent).
- Errors are structured with stable fields (`code`, `message`, optional `details`).

## 2) Godot Process Control
- Godot executable discovery works in this priority:
  1. `GODOT_PATH` env var
  2. executable lookup on `PATH`
  3. common Windows install locations
- Launch editor returns session metadata (`session_id`, `pid`, `status`).
- Run project in debug mode returns session metadata.
- Stop execution handles normal termination and force kill fallback.
- Output capture includes stdout and stderr with timestamps.
- Output retrieval supports bounded history and cursor pagination.

## 3) Project Discovery and Analysis
- Project discovery scans only the caller-provided root path.
- Discovery requires `project.godot`.
- Analysis returns scenes, scripts, resources, plugins/autoload metadata.
- Invalid or missing path returns structured errors.

## 4) Godot Addon Bridge (if included in this wave)
- Local-only binding (`127.0.0.1`).
- Token authentication enforced on bridge endpoints.
- Health endpoint returns bridge and addon version info.
- Scene/UID/render routes exist, even if partially stubbed.

## 5) Render Visibility MVP (if included in this wave)
- On-demand capture returns a valid image path and dimensions.
- Interaction API accepts:
  - mouse click
  - key press
  - camera orbit
- Invalid interaction payloads return structured validation errors.

## 6) Tests and Docs
- Unit tests cover schema validation and process lifecycle edge cases.
- Tests cover debug output cursor/ring buffer behavior.
- README contains run instructions and test instructions.
- Commands used by contributors are documented and reproducible.

## 7) Regression and Safety
- No direct fragile `.tscn` string surgery for scene mutations when addon path is available.
- Paths are normalized and constrained to intended project scope.
- No destructive or unrelated repository changes.
