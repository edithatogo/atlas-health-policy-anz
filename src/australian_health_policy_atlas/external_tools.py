"""Thin, evidence-preserving adapters for SourceRight, CiteWeft and Authentext."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .hashing import sha256_json


@dataclass(frozen=True, slots=True)
class ToolReceipt:
    tool_id: str
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    input_sha256: str


def run_json_tool(
    tool_id: str,
    command: Sequence[str],
    payload: dict[str, Any],
    *,
    cwd: str | Path | None = None,
    timeout_seconds: int = 120,
) -> ToolReceipt:
    """Run an explicitly configured local tool; no shell, no implicit discovery."""
    if not command:
        raise ValueError("tool command must be explicit")
    completed = subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true] - executable is explicit configuration, shell is disabled
        list(command),
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=timeout_seconds,
        check=False,
    )
    return ToolReceipt(
        tool_id=tool_id,
        command=tuple(command),
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        input_sha256=sha256_json(payload),
    )
