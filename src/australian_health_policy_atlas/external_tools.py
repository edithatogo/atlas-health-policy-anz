"""Thin, evidence-preserving adapters for SourceRight, CiteWeft and Authentext."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path


import json
import subprocess  # ruff: ignore[suspicious-subprocess-import] - Bounded argv-only maintenance; no policy text is executed.
from dataclasses import dataclass

from .hashing import sha256_json


@dataclass(frozen=True, slots=True)
class ToolReceipt:
    """Recorded outcome of an explicitly configured local tool invocation."""

    tool_id: str
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    input_sha256: str


def run_json_tool(
    tool_id: str,
    command: Sequence[str],
    payload: Mapping[str, object],
    *,
    cwd: str | Path | None = None,
    timeout_seconds: int = 120,
) -> ToolReceipt:
    """Run an explicitly configured local tool; no shell, no implicit discovery.

    Returns:
        The result described above, retaining the declared return-type contract.

    Raises:
        ValueError: The supplied data violates the function's documented validation
        contract.

    """
    if not command:
        message = "tool command must be explicit"
        raise ValueError(message)
    completed = subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true] - Trusted executable and fixed argv; shell remains disabled.
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
