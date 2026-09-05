from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

import json

import pytest

from australian_health_policy_atlas.model_manifest import load_model_manifest


def write(tmp_path: Path, value: dict[str, object]) -> Path:
    path = tmp_path / "m.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def valid() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "model_id": "m",
        "source_repository": "o/r",
        "revision": "r",
        "artifact": "a.gguf",
        "sha256": "0" * 64,
        "runtime": "llama.cpp",
        "task_classes": ["x"],
        "benchmark_receipts": [],
    }


def test_missing_fields(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="missing fields"):
        load_model_manifest(write(tmp_path, {}))


def test_bad_schema(tmp_path: Path) -> None:
    value = valid()
    value["schema_version"] = "2.0"
    with pytest.raises(ValueError, match="unsupported"):
        load_model_manifest(write(tmp_path, value))


def test_bad_hash(tmp_path: Path) -> None:
    value = valid()
    value["sha256"] = "z" * 64
    with pytest.raises(ValueError, match="sha256"):
        load_model_manifest(write(tmp_path, value))


def test_empty_tasks(tmp_path: Path) -> None:
    value = valid()
    value["task_classes"] = []
    with pytest.raises(ValueError, match="task class"):
        load_model_manifest(write(tmp_path, value))
