"""Managed Godot process sessions with async output capture."""

from __future__ import annotations

import asyncio
import contextlib
import os
import subprocess
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import IO, Literal
from uuid import uuid4

from .errors import MCPError

StreamName = Literal["stdout", "stderr", "system"]


def utc_now_iso() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class OutputEntry:
    """Single line of process output."""

    cursor: int
    timestamp: str
    stream: StreamName
    message: str


class OutputRingBuffer:
    """Bounded line buffer with cursor-based pagination."""

    def __init__(self, max_entries: int = 4000) -> None:
        self._entries: deque[OutputEntry] = deque(maxlen=max_entries)
        self._next_cursor = 1

    def append(self, stream: StreamName, message: str) -> int:
        cursor = self._next_cursor
        self._next_cursor += 1
        self._entries.append(
            OutputEntry(
                cursor=cursor,
                timestamp=utc_now_iso(),
                stream=stream,
                message=message,
            )
        )
        return cursor

    def get_entries(self, *, limit: int, cursor: int | None) -> tuple[list[OutputEntry], int | None]:
        result: list[OutputEntry] = []
        for entry in self._entries:
            if cursor is not None and entry.cursor <= cursor:
                continue
            result.append(entry)
            if len(result) >= limit:
                break
        next_cursor = result[-1].cursor if result else cursor
        return result, next_cursor


class PopenAsyncAdapter:
    """Async-compatible wrapper around subprocess.Popen for Windows fallback."""

    def __init__(self, proc: subprocess.Popen[str]) -> None:
        self._proc = proc

    @property
    def pid(self) -> int | None:
        return self._proc.pid

    @property
    def returncode(self) -> int | None:
        return self._proc.returncode

    @property
    def stdout(self) -> IO[str] | None:
        return self._proc.stdout

    @property
    def stderr(self) -> IO[str] | None:
        return self._proc.stderr

    def terminate(self) -> None:
        self._proc.terminate()

    def kill(self) -> None:
        self._proc.kill()

    async def wait(self) -> int:
        return await asyncio.to_thread(self._proc.wait)


@dataclass(slots=True)
class ProcessSession:
    """Session state for one Godot process."""

    session_id: str
    pid: int
    mode: Literal["editor", "run"]
    project_path: str
    started_at: str
    process: asyncio.subprocess.Process | PopenAsyncAdapter
    output: OutputRingBuffer = field(default_factory=OutputRingBuffer)
    exit_code: int | None = None
    stdout_task: asyncio.Task[None] | None = None
    stderr_task: asyncio.Task[None] | None = None
    waiter_task: asyncio.Task[None] | None = None

    @property
    def status(self) -> Literal["running", "exited"]:
        return "running" if self.exit_code is None else "exited"


class ProcessRegistry:
    """Tracks process sessions and provides lifecycle operations."""

    def __init__(self) -> None:
        self._sessions: dict[str, ProcessSession] = {}
        self._created_order: list[str] = []

    @property
    def sessions(self) -> dict[str, ProcessSession]:
        """Expose session mapping for read-only orchestration."""
        return self._sessions

    async def create_session(
        self,
        *,
        godot_path: Path,
        project_path: Path,
        mode: Literal["editor", "run"],
        headless: bool = False,
        debug: bool = True,
        scene_override: str | None = None,
    ) -> ProcessSession:
        """Launch a Godot process and begin asynchronous output capture."""
        args = [str(godot_path), "--path", str(project_path)]
        if mode == "editor":
            args.append("--editor")
            if headless:
                args.append("--headless")
        elif mode == "run":
            if debug:
                args.append("--verbose")
            if scene_override:
                args.extend(["--main-scene", scene_override])

        process: asyncio.subprocess.Process | PopenAsyncAdapter
        try:
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except PermissionError:
            # Some Windows environments deny async pipe creation for child processes.
            process = self._spawn_with_popen(args)

        session_id = str(uuid4())
        session = ProcessSession(
            session_id=session_id,
            pid=process.pid if process.pid is not None else -1,
            mode=mode,
            project_path=str(project_path),
            started_at=utc_now_iso(),
            process=process,
        )
        session.output.append("system", f"Started command: {' '.join(args)}")

        session.stdout_task = asyncio.create_task(self._read_stream(session, "stdout", process.stdout))
        session.stderr_task = asyncio.create_task(self._read_stream(session, "stderr", process.stderr))
        session.waiter_task = asyncio.create_task(self._wait_for_exit(session))

        self._sessions[session_id] = session
        self._created_order.append(session_id)
        return session

    async def stop_session(self, session_id: str | None = None) -> tuple[bool, int | None]:
        """Stop a specific session or the most recently created running session."""
        session = self._get_session_for_stop(session_id)
        if session is None:
            return False, None
        if session.exit_code is not None:
            return False, session.exit_code

        session.process.terminate()
        try:
            await asyncio.wait_for(session.process.wait(), timeout=8)
        except TimeoutError:
            session.process.kill()
            await session.process.wait()
        finally:
            session.exit_code = session.process.returncode
            session.output.append("system", "Process stop requested.")
        return True, session.exit_code

    def get_output(
        self,
        *,
        session_id: str | None,
        limit: int,
        cursor: int | None,
    ) -> tuple[list[OutputEntry], int | None]:
        """Get buffered output for a target session."""
        session = self._resolve_session(session_id)
        return session.output.get_entries(limit=limit, cursor=cursor)

    def _resolve_session(self, session_id: str | None) -> ProcessSession:
        if session_id:
            if session_id not in self._sessions:
                raise MCPError(
                    code="SESSION_NOT_FOUND",
                    message="Session ID was not found.",
                    details={"session_id": session_id},
                )
            return self._sessions[session_id]

        for sid in reversed(self._created_order):
            session = self._sessions[sid]
            return session
        raise MCPError(
            code="SESSION_NOT_FOUND",
            message="No sessions have been created.",
            details={},
        )

    def _get_session_for_stop(self, session_id: str | None) -> ProcessSession | None:
        try:
            return self._resolve_session(session_id)
        except MCPError:
            return None

    def _spawn_with_popen(self, args: list[str]) -> PopenAsyncAdapter:
        proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        return PopenAsyncAdapter(proc)

    async def _read_stream(
        self,
        session: ProcessSession,
        stream_name: StreamName,
        stream: asyncio.StreamReader | IO[str] | None,
    ) -> None:
        if stream is None:
            return
        while True:
            if isinstance(stream, asyncio.StreamReader):
                line = await stream.readline()
            else:
                line = await asyncio.to_thread(stream.readline)
            if not line:
                break
            if isinstance(line, bytes):
                text = line.decode(errors="replace").rstrip("\r\n")
            else:
                text = str(line).rstrip("\r\n")
            if text:
                session.output.append(stream_name, text)

    async def _wait_for_exit(self, session: ProcessSession) -> None:
        rc = await session.process.wait()
        session.exit_code = rc
        session.output.append("system", f"Process exited with code {rc}.")
        for task in (session.stdout_task, session.stderr_task):
            if task:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task
