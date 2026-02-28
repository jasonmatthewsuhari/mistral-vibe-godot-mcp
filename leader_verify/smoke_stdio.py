from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import Any


def _encode_message(payload: dict[str, Any]) -> bytes:
    body = json.dumps(payload).encode("utf-8")
    return f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body


def _read_message(stdout_pipe) -> dict[str, Any]:
    headers: dict[str, str] = {}
    while True:
        line = stdout_pipe.readline()
        if not line:
            raise RuntimeError("Unexpected EOF while reading headers")
        if line in (b"\r\n", b"\n"):
            break
        key, _, value = line.decode("utf-8").partition(":")
        headers[key.strip().lower()] = value.strip()

    length = int(headers.get("content-length", "0"))
    if length <= 0:
        raise RuntimeError(f"Invalid content-length header: {headers!r}")
    body = stdout_pipe.read(length)
    if len(body) != length:
        raise RuntimeError("Unexpected EOF while reading message body")
    return json.loads(body.decode("utf-8"))


def run_smoke(timeout_seconds: float = 6.0) -> dict[str, Any]:
    proc = subprocess.Popen(
        [sys.executable, "-m", "mcp_server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        assert proc.stdin is not None
        assert proc.stdout is not None
        assert proc.stderr is not None

        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "leader-verify", "version": "0.0.1"},
            },
        }
        proc.stdin.write(_encode_message(init_request))
        proc.stdin.flush()
        if proc.poll() is not None:
            stderr = proc.stderr.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Server exited before initialize response. Stderr:\n{stderr}")
        try:
            init_response = _read_message(proc.stdout)
        except RuntimeError as exc:
            stderr = proc.stderr.read().decode("utf-8", errors="replace") if proc.poll() is not None else ""
            raise RuntimeError(f"{exc}\nStderr:\n{stderr}") from exc

        list_request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        proc.stdin.write(_encode_message(list_request))
        proc.stdin.flush()
        if proc.poll() is not None:
            stderr = proc.stderr.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Server exited before tools/list response. Stderr:\n{stderr}")
        try:
            list_response = _read_message(proc.stdout)
        except RuntimeError as exc:
            stderr = proc.stderr.read().decode("utf-8", errors="replace") if proc.poll() is not None else ""
            raise RuntimeError(f"{exc}\nStderr:\n{stderr}") from exc

        return {"initialize": init_response, "tools_list": list_response}
    finally:
        if proc.stdin:
            proc.stdin.close()
        proc.terminate()
        try:
            proc.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=timeout_seconds)
        if proc.stdout:
            proc.stdout.close()
        if proc.stderr:
            proc.stderr.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-check stdio MCP framing and methods.")
    parser.add_argument("--json", action="store_true", help="Print full JSON response payloads.")
    args = parser.parse_args()

    payload = run_smoke()
    init_result = payload["initialize"].get("result", {})
    tools_result = payload["tools_list"].get("result", {})
    tool_names = sorted(tool.get("name") for tool in tools_result.get("tools", []))

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("stdio smoke:")
        print(f"initialize.protocolVersion={init_result.get('protocolVersion')}")
        print(f"tools.count={len(tool_names)}")
        print(f"tools={tool_names}")

    ok = bool(init_result.get("protocolVersion")) and bool(tool_names)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
