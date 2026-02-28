from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from typing import Any


def _encode_frame(payload: dict[str, Any]) -> bytes:
    body = json.dumps(payload).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
    return header + body


def _read_frame(stdout_pipe) -> dict[str, Any]:
    headers: dict[str, str] = {}
    while True:
        line = stdout_pipe.readline()
        if not line:
            raise RuntimeError("EOF while reading response headers")
        if line in (b"\r\n", b"\n"):
            break
        key, _, value = line.decode("utf-8").partition(":")
        headers[key.strip().lower()] = value.strip()

    content_length = int(headers.get("content-length", "0"))
    if content_length <= 0:
        raise RuntimeError(f"Invalid Content-Length: {headers!r}")
    body = stdout_pipe.read(content_length)
    if len(body) != content_length:
        raise RuntimeError("EOF while reading response body")
    return json.loads(body.decode("utf-8"))


@dataclass
class MCPStdioClient:
    process: subprocess.Popen[bytes]

    @classmethod
    def start(cls) -> "MCPStdioClient":
        env = dict(os.environ)
        process = subprocess.Popen(
            [sys.executable, "-m", "mcp_server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
        return cls(process=process)

    def request(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.process.stdin or not self.process.stdout:
            raise RuntimeError("stdio pipes are unavailable")
        self.process.stdin.write(_encode_frame(payload))
        self.process.stdin.flush()
        if self.process.poll() is not None:
            stderr = self.read_stderr()
            raise RuntimeError(f"mcp_server exited unexpectedly before response:\n{stderr}")
        return _read_frame(self.process.stdout)

    def initialize(self) -> dict[str, Any]:
        return self.request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "leader-integration", "version": "0.1.0"},
                },
            }
        )

    def list_tools(self) -> dict[str, Any]:
        return self.request({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})

    def call_tool(self, tool_name: str, arguments: dict[str, Any] | None = None, req_id: int = 3) -> dict[str, Any]:
        return self.request(
            {
                "jsonrpc": "2.0",
                "id": req_id,
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": arguments or {}},
            }
        )

    def read_stderr(self) -> str:
        if not self.process.stderr:
            return ""
        return self.process.stderr.read().decode("utf-8", errors="replace")

    def close(self) -> None:
        if self.process.stdin:
            self.process.stdin.close()
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=6)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=6)
        if self.process.stdout:
            self.process.stdout.close()
        if self.process.stderr:
            self.process.stderr.close()

