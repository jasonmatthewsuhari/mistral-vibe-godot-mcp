# Release Notes Draft - v0.1.0

## Delivered Summary
- Wave 1 foundation:
  - Replaced legacy protocol scaffold with stdio MCP server transport.
  - Added typed Pydantic contracts for core Godot process and project tools.
  - Added Windows-first Godot executable discovery and process session registry with cursor-based debug buffer retrieval.
  - Added project discovery and static project analysis support.
- Wave 2 tooling:
  - Wired scene, UID, and render tools end-to-end through localhost token-auth bridge client.
  - Added strict validation for `render_interact` mode payloads.
  - Standardized failure mapping to canonical `MCPError` shape (`code`, `message`, `details`).
- Wave 3 scaffolding:
  - Added CI quality gate workflow with smoke + audit + unittest checks and tool-list artifact publication.
  - Added optional integration CI job and artifact capture for integration logs.
  - Added machine-readable tool manifest and parity validation script.

## Verification Snapshot
- Main quality gate:
  - `python -m pytest -q`: PASS (`49 passed, 5 skipped`)
  - `python -m leader_verify.audit_wave2 --json`: PASS (`ok=true`)
  - `python -m leader_verify.smoke_stdio --json`: PASS (initialize + tools/list with 16 tools)
- Integration gate (Team B run, from `RELEASE_CHECKLIST.md`):
  - `python -m pytest -q tests_integration -m godot_integration`: `1 failed, 3 passed`
  - Failing test: `tests_integration/test_godot_runtime_integration.py::test_scene_uid_render_end_to_end`
  - Failure summary: bridge health timeout during startup.

## Known Limitations
- Integration tests require a real Godot 4.4+ runtime and local bridge setup; they are opt-in.
- Bridge operations depend on addon availability and token configuration in target project.
- CI default job validates API surface and stdio behavior but does not prove full engine/runtime behavior without integration gating enabled.
- Manifest is committed artifact and should be regenerated when tool signatures or names change.
- One integration scenario remains flaky/failing in Team B result (bridge health timeout path).

## Minimum Runtime Requirements
- Python 3.11+
- `pydantic` installed in runtime environment
- Godot 4.4+ for runtime process/bridge operations
- MCP client capable of stdio JSON-RPC framing (`Content-Length` transport)
