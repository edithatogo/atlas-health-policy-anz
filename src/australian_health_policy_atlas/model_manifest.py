"""Pinned local-model qualification manifests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REQUIRED = {
    "schema_version",
    "model_id",
    "source_repository",
    "revision",
    "artifact",
    "sha256",
    "runtime",
    "task_classes",
    "benchmark_receipts",
}


def load_model_manifest(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    missing = sorted(REQUIRED - set(value))
    if missing:
        raise ValueError(f"model manifest missing fields: {missing}")
    if value["schema_version"] != "1.0":
        raise ValueError("unsupported model manifest schema")
    digest = value["sha256"]
    if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
        raise ValueError("model sha256 must be lowercase hex")
    if not value["task_classes"]:
        raise ValueError("model manifest must declare at least one task class")
    return value
