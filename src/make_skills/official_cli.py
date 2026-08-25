"""Minimal, secret-safe bridge to the official Make CLI."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence


class OfficialCliError(RuntimeError):
    """The official Make CLI could not be found or complete a command."""


@dataclass(frozen=True)
class CommandResult:
    arguments: tuple[str, ...]
    stdout: str
    stderr: str


def locate(executable: str | None = None) -> str:
    """Find the official binary without installing or downloading anything."""
    candidate = executable or os.environ.get("MAKE_SKILLS_MAKE_CLI") or shutil.which("make-cli")
    if not candidate:
        raise OfficialCliError(
            "Official make-cli was not found. Install it from the Make CLI documentation "
            "or set MAKE_SKILLS_MAKE_CLI to its executable path."
        )
    path = Path(candidate).expanduser()
    if path.parent != Path(".") and not path.is_file():
        raise OfficialCliError(f"Official make-cli does not exist: {path}")
    return str(path) if path.parent != Path(".") else candidate


def run(arguments: Sequence[str], executable: str | None = None) -> CommandResult:
    """Run the official CLI and return its output; never include credentials in arguments."""
    command = [locate(executable), *arguments]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip() or f"exit status {completed.returncode}"
        raise OfficialCliError(f"Official make-cli {' '.join(arguments)} failed: {detail}")
    return CommandResult(tuple(arguments), completed.stdout, completed.stderr)


def run_json(arguments: Sequence[str], executable: str | None = None) -> Any:
    """Run a Make CLI read command that produces its default JSON output."""
    output = run(arguments, executable).stdout
    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        raise OfficialCliError("Official make-cli returned non-JSON output; omit --output table/compact.") from exc


def list_items(value: Any, preferred_keys: Sequence[str]) -> list[dict[str, Any]]:
    """Normalize common Make collection envelopes without assuming one fixed shape."""
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        for key in preferred_keys:
            nested = value.get(key)
            if isinstance(nested, list):
                return [item for item in nested if isinstance(item, dict)]
    return []


def label(item: dict[str, Any]) -> str:
    """Return a concise identifier without serializing an entire API response."""
    identifier = item.get("id", "?")
    name = item.get("name") or item.get("label") or item.get("title") or "unnamed"
    return f"{identifier}: {name}"
