"""Discovery for Godot executable paths (Windows-first)."""

from __future__ import annotations

import os
import shutil
from glob import glob
from pathlib import Path
from typing import Iterable

from .errors import MCPError

ENV_CANDIDATES = ("GODOT_PATH", "GODOT_EXECUTABLE")
PATH_CANDIDATES = ("godot", "godot4", "Godot_v4.4-stable_win64.exe")


def _candidate_paths() -> Iterable[Path]:
    for env_name in ENV_CANDIDATES:
        raw = os.environ.get(env_name)
        if raw:
            yield Path(raw).expanduser()

    for command in PATH_CANDIDATES:
        found = shutil.which(command)
        if found:
            yield Path(found)

    if os.name == "nt":
        windows_patterns = (
            r"C:\Program Files\Godot*\Godot*.exe",
            r"C:\Program Files\Godot Engine\godot.exe",
            r"C:\Program Files (x86)\Godot*\Godot*.exe",
            r"C:\Users\*\AppData\Local\Programs\Godot*\Godot*.exe",
            r"C:\Users\*\Downloads\Godot*\Godot*.exe",
        )
        for pattern in windows_patterns:
            for match in glob(pattern):
                yield Path(match)


def discover_godot_executable() -> Path:
    """Find a valid Godot executable with clear precedence and errors."""
    inspected: list[str] = []
    for candidate in _candidate_paths():
        candidate = candidate.resolve()
        inspected.append(str(candidate))
        if candidate.exists() and candidate.is_file():
            return candidate

    raise MCPError(
        code="GODOT_NOT_FOUND",
        message="Unable to find a Godot executable.",
        details={
            "inspected_candidates": inspected,
            "hint": "Set GODOT_PATH or install Godot and ensure it is on PATH.",
        },
    )
