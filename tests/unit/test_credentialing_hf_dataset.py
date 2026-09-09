from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import cast

ROOT = Path(__file__).parents[2]
BUILDER = ROOT / "scripts" / "build_credentialing_hf_dataset.py"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def test_public_credentialing_dataset_builds_fail_closed(tmp_path: Path) -> None:
    output = tmp_path / "credentialing-policy-atlas"
    completed = subprocess.run(
        [sys.executable, str(BUILDER), "--output", str(output)],
        check=True,
        capture_output=True,
        text=True,
    )
    receipt = cast("dict[str, object]", json.loads(completed.stdout))

    assert receipt["source_rows"] == 8
    assert receipt["model_scope_rows"] == 88
    assert receipt["final_model_rows"] == 83
    assert receipt["under_review_rows"] == 5
    assert receipt["contains_source_binaries"] is False
    assert receipt["contains_personal_or_operational_data"] is False

    with (output / "data" / "model_scopes.csv").open(
        encoding="utf-8",
        newline="",
    ) as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 88
    assert not list(output.rglob("*.pdf"))
    assert not list(output.rglob("*.docx"))

    manifest_lines = (output / "MANIFEST.sha256").read_text(
        encoding="utf-8",
    ).splitlines()
    assert manifest_lines
    for line in manifest_lines:
        expected, relative_path = line.split("  ", maxsplit=1)
        assert _sha256(output / relative_path) == expected
