import json
from pathlib import Path

from australian_health_policy_atlas.cli import main


def test_doctor(capsys: object) -> None:
    assert main(["doctor"]) == 0


def test_bronze_cli(tmp_path: Path, capsys: object) -> None:
    source = tmp_path / "x.txt"
    source.write_text("x", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    assert main([
        "bronze-ingest",
        str(source),
        "--source-id", "x",
        "--source-uri", "https://example.test/x",
        "--cas-root", str(tmp_path / "cas"),
        "--manifest", str(manifest),
    ]) == 0
    value = json.loads(manifest.read_text(encoding="utf-8"))
    assert value["record_count"] == 1
