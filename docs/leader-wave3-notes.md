# Leader Wave 3 Notes

Independent additions for integration readiness:

- `leader_integration/stdio_client.py`: framed stdio JSON-RPC client for MCP server smoke/live tests.
- `leader_integration/fixtures/minimal_project`: minimal Godot project fixture.
- `leader_integration_tests/`:
  - `test_stdio_harness.py`: always-on handshake and tool listing smoke test.
  - `test_live_optin.py`: env-gated live tool checks (`ENABLE_LEADER_GODOT_INTEGRATION=1`).
- `tests_integration/__init__.py`: package marker to fix relative-import collection errors.
- `scripts/run-full-verification.ps1`: one-command verification runner.

## Commands

```powershell
python -m pytest -q
python -m leader_verify.audit_wave2 --json
python -m leader_verify.smoke_stdio
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run-full-verification.ps1
```

Optional live suite:

```powershell
$env:ENABLE_LEADER_GODOT_INTEGRATION = "1"
python -m unittest discover -s leader_integration_tests -v
```

