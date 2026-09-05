"""Build and verify content-addressed offline comparison bundles."""

from __future__ import annotations

import json
import shutil
from collections.abc import Iterable
from pathlib import Path

from .hashing import sha256_file, sha256_json


def build_bundle(
    *,
    files: Iterable[str | Path],
    output_dir: str | Path,
    bundle_id: str,
) -> dict[str, object]:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []
    for item in files:
        source = Path(item)
        relative = Path("payload") / source.name
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        records.append({
            "path": str(relative).replace("\\", "/"),
            "sha256": sha256_file(target),
            "size_bytes": target.stat().st_size,
        })
    manifest: dict[str, object] = {
        "schema_version": "1.0",
        "bundle_id": bundle_id,
        "files": sorted(records, key=lambda row: str(row["path"])),
    }
    manifest["manifest_sha256"] = sha256_json(manifest)
    (root / "bundle-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def verify_bundle(root: str | Path) -> tuple[bool, tuple[str, ...]]:
    base = Path(root)
    manifest = json.loads((base / "bundle-manifest.json").read_text(encoding="utf-8"))
    failures: list[str] = []
    expected_manifest_sha = manifest.pop("manifest_sha256")
    if sha256_json(manifest) != expected_manifest_sha:
        failures.append("manifest_identity_mismatch")
    for record in manifest["files"]:
        path = base / record["path"]
        if not path.exists():
            failures.append(f"missing:{record['path']}")
        elif sha256_file(path) != record["sha256"]:
            failures.append(f"sha256_mismatch:{record['path']}")
    return (not failures, tuple(failures))
