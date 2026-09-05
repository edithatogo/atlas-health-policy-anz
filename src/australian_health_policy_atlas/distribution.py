"""Deterministic portable application construction with bundled registries."""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

from .integrity import atomic_bytes
from .hashing import sha256_file


PACKAGE = "australian_health_policy_atlas"


def build_zipapp(repo: Path, destination: Path) -> dict[str, object]:
    package = repo / "src" / PACKAGE
    if not (package / "cli.py").is_file():
        raise ValueError("source package is missing")
    files: dict[str, bytes] = {"__main__.py": (
        f"from {PACKAGE}.cli import main\nraise SystemExit(main())\n").encode()}
    for path in sorted(package.rglob("*.py")):
        if "__pycache__" in path.parts or path.is_symlink():
            continue
        files[f"{PACKAGE}/{path.relative_to(package).as_posix()}"] = path.read_bytes()
    for path in sorted((repo / "data" / "sources").glob("*")):
        if path.suffix not in {".json", ".csv"}:
            continue
        if path.is_symlink():
            raise ValueError("registry symlinks are forbidden")
        files[f"{PACKAGE}/_data/{path.name}"] = path.read_bytes()
    if f"{PACKAGE}/_data/jurisdictions-v1.json" not in files:
        raise ValueError("portable registry missing")
    output = io.BytesIO()
    output.write(b"#!/usr/bin/env python3\n")
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(files.items()):
            item = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            item.compress_type = zipfile.ZIP_DEFLATED
            item.create_system = 3
            item.external_attr = 0o100644 << 16
            archive.writestr(item, data)
    atomic_bytes(destination, output.getvalue())
    return {"sha256": sha256_file(destination), "size_bytes": destination.stat().st_size,
            "members": len(files), "runtime_qualified": False}
