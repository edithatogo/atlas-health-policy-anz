"""Content identity helpers used throughout the Atlas."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def canonical_json_bytes(value: object) -> bytes:
    """Return deterministic UTF-8 JSON bytes for hashing and receipts.

    Returns:
        Deterministic UTF-8 JSON bytes with sorted keys.

    """
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    """Hash the exact supplied bytes with SHA-256.

    Returns:
        The lowercase hexadecimal digest of the exact bytes.

    """
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    """Hash the UTF-8 encoding of the unchanged input text.

    Returns:
        The lowercase hexadecimal digest of the UTF-8 input.

    """
    return sha256_bytes(text.encode("utf-8"))


def sha256_json(value: object) -> str:
    """Hash the canonical JSON representation of the supplied value.

    Returns:
        The lowercase hexadecimal digest of canonical JSON bytes.

    """
    return sha256_bytes(canonical_json_bytes(value))


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    """Hash a file incrementally without loading the whole object into memory.

    Returns:
        The lowercase hexadecimal digest of the file contents.

    """
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()
