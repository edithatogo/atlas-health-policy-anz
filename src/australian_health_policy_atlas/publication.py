"""Build deterministic Hugging Face dataset publication candidates."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from .hashing import sha256_file, sha256_json


def build_bronze_hf_candidate(
    bronze_manifest: dict[str, Any],
    *,
    output_dir: str | Path,
    dataset_id: str,
) -> dict[str, Any]:
    root = Path(output_dir)
    data_root = root / "data" / "objects"
    data_root.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for record in bronze_manifest.get("objects", []):
        source = Path(record["stored_path"])
        target = data_root / record["sha256"]
        if not target.exists():
            shutil.copyfile(source, target)
        if sha256_file(target) != record["sha256"]:
            raise OSError("publication candidate fixity failure")
        row = dict(record)
        row["dataset_path"] = str(target.relative_to(root))
        row.pop("stored_path", None)
        rows.append(row)
    manifest_path = root / "bronze-manifest.jsonl"
    manifest_path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    readme = root / "README.md"
    readme.write_text(
        "---\nlicense: other\npretty_name: Australian Health Policy Atlas Bronze\n---\n\n"
        "# Australian Health Policy Atlas — Bronze\n\n"
        f"Dataset target: `{dataset_id}`. This candidate contains immutable captured source objects plus provenance metadata. "
        "The dataset card does not claim corpus completeness beyond the pinned release manifest.\n",
        encoding="utf-8",
    )
    receipt = {
        "schema_version": "1.0",
        "dataset_id": dataset_id,
        "record_count": len(rows),
        "manifest_sha256": sha256_file(manifest_path),
        "readme_sha256": sha256_file(readme),
    }
    receipt["candidate_sha256"] = sha256_json(receipt)
    (root / "publication-receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt
