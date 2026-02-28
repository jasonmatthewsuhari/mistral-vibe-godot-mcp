from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class DebugEntry:
    idx: int
    timestamp: str
    stream: str
    message: str


class DebugRingBuffer:
    def __init__(self, max_entries: int = 1000) -> None:
        if max_entries <= 0:
            raise ValueError("max_entries must be greater than zero")
        self.max_entries = max_entries
        self._entries: deque[DebugEntry] = deque(maxlen=max_entries)
        self._next_idx = 0

    def append(self, stream: str, message: str, timestamp: str | None = None) -> DebugEntry:
        ts = timestamp or datetime.now(timezone.utc).isoformat()
        entry = DebugEntry(idx=self._next_idx, timestamp=ts, stream=stream, message=message)
        self._entries.append(entry)
        self._next_idx += 1
        return entry

    def get(self, limit: int = 200, cursor: int | None = None) -> dict[str, Any]:
        if limit <= 0:
            raise ValueError("limit must be greater than zero")

        entries = list(self._entries)
        if not entries:
            return {"entries": [], "next_cursor": cursor}

        min_cursor = entries[0].idx
        start = min_cursor if cursor is None else max(cursor, min_cursor)
        selected = [e for e in entries if e.idx >= start][:limit]
        next_cursor = selected[-1].idx + 1 if selected else start

        return {
            "entries": [
                {
                    "idx": e.idx,
                    "timestamp": e.timestamp,
                    "stream": e.stream,
                    "message": e.message,
                }
                for e in selected
            ],
            "next_cursor": next_cursor,
        }

