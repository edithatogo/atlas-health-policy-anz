"""Strict, content-addressed contracts for persisted operational state.

A self-hash detects changes; it is not a signature or evidence of correctness.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping


import os
import re
import tempfile
from pathlib import Path, PurePosixPath

from .hashing import canonical_json_bytes, sha256_json
from .records import decode_json, record

SHA256 = re.compile(r"^[0-9a-f]{64}$")
REVISION = re.compile(r"^[0-9a-f]{40}$")
IDENTIFIER = re.compile(r"^[a-z][a-z0-9-]{0,95}$")


def sealed(value: Mapping[str, object]) -> dict[str, object]:
    """Return a new object with a canonical self-hash.

    Returns:
        A new dictionary with a canonical self-hash, not a signature.

    """
    body = {key: item for key, item in value.items() if key != "sha256"}
    return {**body, "sha256": sha256_json(body)}


def verify_seal(value: Mapping[str, object]) -> None:
    """Reject a persisted object whose canonical self-hash does not match its content.

    Raises:
        ValueError: The supplied data violates the function's documented validation
        contract.

    """
    if not isinstance(value, dict) or value.get("sha256") != sealed(value)["sha256"]:
        message = "invalid self-hash"
        raise ValueError(message)


def read_json(data: bytes) -> dict[str, object]:
    """Decode a strict JSON object; reject duplicates and non-finite constants.

    Returns:
        The result described above, retaining the declared return-type contract.

    Raises:
        ValueError: The supplied data violates the function's documented validation
        contract.

    """
    try:
        return record(decode_json(data))
    except TypeError as exc:
        message = "JSON object required"
        raise ValueError(message) from exc


def safe_path(root: Path, relative: str) -> Path:
    """Resolve a canonical relative path while rejecting traversal and symlink escapes.

    Returns:
        The contained path, without creating or opening the referenced file.

    Raises:
        ValueError: The supplied data violates the function's documented validation
        contract.

    """
    path = PurePosixPath(relative)
    unsafe_components = path.is_absolute() or ".." in path.parts
    ambiguous_spelling = "\\" in relative or ":" in relative or str(path) != relative
    if not relative or relative == "." or unsafe_components or ambiguous_spelling:
        message = "unsafe relative path"
        raise ValueError(message)
    candidate = root / path
    for parent in [candidate, *candidate.parents]:
        if parent == root.parent:
            break
        if parent.is_symlink():
            message = "symlinks are not permitted"
            raise ValueError(message)
    if not candidate.resolve().is_relative_to(root.resolve()):
        message = "path escapes root"
        raise ValueError(message)
    return candidate


def atomic_bytes(path: Path, data: bytes) -> None:
    """Write and flush bytes through a temporary file before atomic replacement."""
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


def atomic_json(path: Path, value: Mapping[str, object]) -> None:
    """Atomically persist canonical JSON with a trailing newline."""
    atomic_bytes(path, canonical_json_bytes(value) + b"\n")
