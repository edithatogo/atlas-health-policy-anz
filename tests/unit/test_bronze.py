from pathlib import Path

from australian_health_policy_atlas.bronze import ingest_local_file, write_manifest
from australian_health_policy_atlas.hashing import sha256_file


def test_bronze_ingest_preserves_bytes(tmp_path: Path) -> None:
    source = tmp_path / "policy.txt"
    source.write_text("Policy text", encoding="utf-8")
    obj = ingest_local_file(
        source,
        source_id="p1",
        source_uri="https://example.test/p1",
        cas_root=tmp_path / "cas",
        observed_at="2026-09-03T00:00:00+00:00",
    )
    assert sha256_file(obj.stored_path) == obj.sha256
    manifest = write_manifest([obj], tmp_path / "manifest.json", release_id="b1")
    assert manifest["record_count"] == 1
    assert len(str(manifest["manifest_sha256"])) == 64
