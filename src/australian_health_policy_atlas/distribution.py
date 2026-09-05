"""Deterministic portable application construction with bundled registries."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


import io
import zipfile

from .hashing import sha256_file
from .integrity import atomic_bytes

PACKAGE = "australian_health_policy_atlas"


def build_zipapp(repo: Path, destination: Path) -> dict[str, object]:
    """Build a deterministic portable runner with its governed source registries.

    Returns:
        Portable artifact identity, size and bundled-source metadata.

    Raises:
        ValueError: The supplied data violates the function's documented validation
        contract.

    """
    package = repo / "src" / PACKAGE
    if not (package / "cli.py").is_file():
        message = "source package is missing"
        raise ValueError(message)
    files: dict[str, bytes] = {
        "__main__.py": (
            f"from {PACKAGE}.cli import main\nraise SystemExit(main())\n"
        ).encode()
    }
    files.update(_source_files(package))
    files.update(_registry_files(repo))
    if f"{PACKAGE}/_data/jurisdictions-v1.json" not in files:
        message = "portable registry missing"
        raise ValueError(message)
    output = io.BytesIO()
    output.write(b"#!/usr/bin/env python3\n")
    with zipfile.ZipFile(
        output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for name, data in sorted(files.items()):
            item = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            item.compress_type = zipfile.ZIP_DEFLATED
            item.create_system = 3
            item.external_attr = 0o100644 << 16
            archive.writestr(item, data)
    atomic_bytes(destination, output.getvalue())
    return {
        "sha256": sha256_file(destination),
        "size_bytes": destination.stat().st_size,
        "members": len(files),
        "runtime_qualified": False,
    }


def _source_files(package: Path) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    for path in sorted(package.rglob("*.py")):
        if "__pycache__" in path.parts or path.is_symlink():
            continue
        files[f"{PACKAGE}/{path.relative_to(package).as_posix()}"] = path.read_bytes()
    return files


def _registry_files(repo: Path) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    for path in sorted((repo / "data" / "sources").glob("*")):
        if path.suffix not in {".json", ".csv"}:
            continue
        if path.is_symlink():
            message = "registry symlinks are forbidden"
            raise ValueError(message)
        files[f"{PACKAGE}/_data/{path.name}"] = path.read_bytes()
    return files
