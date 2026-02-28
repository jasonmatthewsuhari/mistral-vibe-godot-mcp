# Leader Impl Usage (Isolated Track)

This document describes the independent implementation under `leader_impl/`.

## Start server

```powershell
python -m leader_impl.main
```

The server reads one JSON-RPC request per line on `stdin` and writes one JSON-RPC response per line on `stdout`.

## Example requests

### List projects

```json
{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"godot_list_projects","arguments":{"root_path":"C:\\\\Games"}}}
```

### Analyze project

```json
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"godot_analyze_project","arguments":{"project_path":"C:\\\\Games\\\\MyProject"}}}
```

### Render interaction (camera orbit)

```json
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"render_interact","arguments":{"project_path":"C:\\\\Games\\\\MyProject","mode":"camera_orbit","payload":{"dx":12,"dy":-8}}}}
```

## Bridge configuration

Optional env vars:

- `LEADER_BRIDGE_PORT` (default `8799`)
- `LEADER_BRIDGE_TOKEN` (Bearer token for bridge auth)

## Run independent tests

```powershell
python -m unittest discover -s leader_impl_tests -v
```

