"""Structured error types for the MCP server."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class MCPError(Exception):
    """Application error with stable code/message/details structure."""

    code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation of the error."""
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }


def make_error(code: str, message: str, details: dict[str, Any] | None = None) -> MCPError:
    """Create a structured MCPError with optional details."""
    return MCPError(code=code, message=message, details=details or {})
