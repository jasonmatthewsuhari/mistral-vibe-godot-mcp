"""Minimal MCP stdio JSON-RPC server implementation."""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from typing import Any

from pydantic import BaseModel

from .errors import MCPError
from .tools import GodotToolService, ToolDefinition, parse_arguments

LOGGER = logging.getLogger("mcp_server")


class StdioMCPServer:
    """MCP server over stdio using Content-Length framed JSON-RPC messages."""

    def __init__(self) -> None:
        self.tool_service = GodotToolService()
        self.tools = self.tool_service.get_definitions()

    async def run(self) -> None:
        """Read requests forever and write JSON-RPC responses."""
        while True:
            message = await asyncio.to_thread(self._read_message)
            if message is None:
                return
            await self._handle_message(message)

    async def _handle_message(self, message: dict[str, Any]) -> None:
        method = message.get("method")
        message_id = message.get("id")
        params = message.get("params") or {}

        if method == "notifications/initialized":
            return
        if method == "ping":
            if message_id is not None:
                self._write_response({"jsonrpc": "2.0", "id": message_id, "result": {}})
            return
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "mistral-vibe-godot-mcp", "version": "0.1.0"},
            }
            self._write_response({"jsonrpc": "2.0", "id": message_id, "result": result})
            return
        if method == "tools/list":
            result = {"tools": [self._tool_descriptor(tool) for tool in self.tools.values()]}
            self._write_response({"jsonrpc": "2.0", "id": message_id, "result": result})
            return
        if method == "tools/call":
            await self._handle_tool_call(message_id, params)
            return

        if message_id is not None:
            self._write_error(
                message_id=message_id,
                jsonrpc_code=-32601,
                message="Method not found.",
                data={"method": method},
            )

    async def _handle_tool_call(self, message_id: Any, params: dict[str, Any]) -> None:
        name = params.get("name")
        arguments = params.get("arguments")
        if name not in self.tools:
            self._write_error(
                message_id=message_id,
                jsonrpc_code=-32602,
                message="Unknown tool name.",
                data={"name": name},
            )
            return

        tool = self.tools[name]
        try:
            parsed_request = parse_arguments(tool.request_model, arguments)
            output_model = await tool.handler(parsed_request)
            if not isinstance(output_model, BaseModel):
                raise MCPError(
                    code="INTERNAL_ERROR",
                    message="Tool handler returned unexpected response type.",
                    details={"tool": name, "type": type(output_model).__name__},
                )
            payload = output_model.model_dump()
            self._write_response(
                {
                    "jsonrpc": "2.0",
                    "id": message_id,
                    "result": {
                        "structuredContent": payload,
                        "content": [{"type": "text", "text": json.dumps(payload)}],
                        "isError": False,
                    },
                }
            )
        except MCPError as exc:
            self._write_response(
                {
                    "jsonrpc": "2.0",
                    "id": message_id,
                    "result": {
                        "isError": True,
                        "content": [{"type": "text", "text": exc.message}],
                        "structuredContent": {"error": exc.to_dict()},
                    },
                }
            )
        except Exception as exc:  # pragma: no cover - defensive fallback
            LOGGER.exception("Unhandled tool exception")
            self._write_response(
                {
                    "jsonrpc": "2.0",
                    "id": message_id,
                    "result": {
                        "isError": True,
                        "content": [{"type": "text", "text": "Unhandled server error."}],
                        "structuredContent": {
                            "error": {
                                "code": "INTERNAL_ERROR",
                                "message": "Unhandled server error.",
                                "details": {"reason": str(exc)},
                            }
                        },
                    },
                }
            )

    def _tool_descriptor(self, tool: ToolDefinition) -> dict[str, Any]:
        return {
            "name": tool.name,
            "description": tool.description,
            "inputSchema": tool.request_model.model_json_schema(),
        }

    def _read_message(self) -> dict[str, Any] | None:
        headers: dict[str, str] = {}
        while True:
            line = sys.stdin.buffer.readline()
            if not line:
                return None
            if line in (b"\r\n", b"\n"):
                break
            key, _, value = line.decode("utf-8").partition(":")
            headers[key.strip().lower()] = value.strip()

        length_raw = headers.get("content-length")
        if not length_raw:
            return None

        body = sys.stdin.buffer.read(int(length_raw))
        if not body:
            return None
        return json.loads(body.decode("utf-8"))

    def _write_response(self, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        header = f"Content-Length: {len(encoded)}\r\n\r\n".encode("ascii")
        sys.stdout.buffer.write(header + encoded)
        sys.stdout.buffer.flush()

    def _write_error(self, *, message_id: Any, jsonrpc_code: int, message: str, data: dict[str, Any]) -> None:
        self._write_response(
            {
                "jsonrpc": "2.0",
                "id": message_id,
                "error": {"code": jsonrpc_code, "message": message, "data": data},
            }
        )

