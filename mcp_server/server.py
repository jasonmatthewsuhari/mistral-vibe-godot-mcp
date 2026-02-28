"""Entrypoint for the stdio MCP server."""

from __future__ import annotations

import asyncio
import logging

from .stdio_server import StdioMCPServer


def configure_logging() -> None:
    """Configure minimal stderr logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


async def main() -> None:
    """Start the stdio server loop."""
    configure_logging()
    server = StdioMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())

