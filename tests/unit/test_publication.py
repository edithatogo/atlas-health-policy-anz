from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


from australian_health_policy_atlas.bronze import ingest_local_file, write_manifest
from australian_health_policy_atlas.publication import build_bronze_hf_candidate


def test_hf_candidate_replays_bronze_bytes(tmp_path: Path) -> None:
    source = tmp_path / "policy.txt"
    source.write_text("policy", encoding="utf-8")
    obj = ingest_local_file(
        source,
        source_id="p",
        source_uri="https://example.test/p",
        cas_root=tmp_path / "cas",
        observed_at="2026-09-03T00:00:00+00:00",
    )
    manifest = write_manifest([obj], tmp_path / "manifest.json", release_id="b1")
    receipt = build_bronze_hf_candidate(
        manifest, output_dir=tmp_path / "hf", dataset_id="edithatogo/test"
    )
    assert receipt["record_count"] == 1
    assert (tmp_path / "hf" / "bronze-manifest.jsonl").exists()
