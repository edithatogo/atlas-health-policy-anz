"""Strict, content-addressed contracts for persisted operational state.

A self-hash detects changes; it is not a signature or evidence of correctness.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

from .hashing import canonical_json_bytes, sha256_json

SHA256 = re.compile(r"^[0-9a-f]{64}$")
REVISION = re.compile(r"^[0-9a-f]{40}$")
IDENTIFIER = re.compile(r"^[a-z][a-z0-9-]{0,95}$")


def sealed(value: dict[str, Any]) -> dict[str, Any]:
    """Return a new object with a canonical self-hash."""
    body = {key: item for key, item in value.items() if key != "sha256"}
    return {**body, "sha256": sha256_json(body)}


def verify_seal(value: dict[str, Any]) -> None:
    if not isinstance(value, dict) or value.get("sha256") != sealed(value)["sha256"]:
        raise ValueError("invalid self-hash")


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _bad_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant: {value}")


def read_json(data: bytes) -> dict[str, Any]:
    value = json.loads(data, object_pairs_hook=_pairs, parse_constant=_bad_constant)
    if not isinstance(value, dict):
        raise ValueError("JSON object required")
    return value


def safe_path(root: Path, relative: str) -> Path:
    path = PurePosixPath(relative)
    if (
        not relative
        or relative == "."
        or path.is_absolute()
        or ".." in path.parts
        or "\\" in relative
        or ":" in relative
        or str(path) != relative
    ):
        raise ValueError("unsafe relative path")
    candidate = root / path
    for parent in [candidate, *candidate.parents]:
        if parent == root.parent:
            break
        if parent.is_symlink():
            raise ValueError("symlinks are not permitted")
    if not candidate.resolve().is_relative_to(root.resolve()):
        raise ValueError("path escapes root")
    return candidate


def atomic_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=".atlas-", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        Path(temporary).replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    atomic_bytes(path, canonical_json_bytes(value) + b"\n")
