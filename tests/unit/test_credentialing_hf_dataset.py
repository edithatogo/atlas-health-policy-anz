from __future__ import annotations

import csv
import hashlib
from pathlib import Path

from scripts.build_credentialing_hf_dataset import build_dataset


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def test_public_credentialing_dataset_builds_fail_closed(tmp_path: Path) -> None:
    output = tmp_path / "credentialing-policy-atlas"
    receipt = build_dataset(output)

    assert receipt["source_rows"] == 14
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

    manifest_lines = (
        (output / "MANIFEST.sha256")
        .read_text(
            encoding="utf-8",
        )
        .splitlines()
    )
    assert manifest_lines
    for line in manifest_lines:
        expected, relative_path = line.split("  ", maxsplit=1)
        assert _sha256(output / relative_path) == expected
