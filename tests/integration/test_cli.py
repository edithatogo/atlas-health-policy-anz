from __future__ import annotations

import json
import pathlib
from pathlib import Path

import pytest

from australian_health_policy_atlas.cli import main


def test_doctor(capsys: object) -> None:
    assert main(["doctor"]) == 0


def test_bronze_cli(tmp_path: Path, capsys: object) -> None:
    source = tmp_path / "x.txt"
    source.write_text("x", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    assert (
        main([
            "bronze-ingest",
            str(source),
            "--source-id",
            "x",
            "--source-uri",
            "https://example.test/x",
            "--cas-root",
            str(tmp_path / "cas"),
            "--manifest",
            str(manifest),
        ])
        == 0
    )
    value = json.loads(manifest.read_text(encoding="utf-8"))
    assert value["record_count"] == 1


def test_cli_nlp_and_graph_query(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from australian_health_policy_atlas.graph import build_policy_graph, write_graph
    from australian_health_policy_atlas.silver import normalize_text

    assert main(["nlp-analyse", "Nurses must escalate care."]) == 0
    nlp_payload = json.loads(capsys.readouterr().out)
    assert nlp_payload["engine"] == "spacy"

    graph = build_policy_graph(
        segments=normalize_text("src", "Nurses must escalate care.")
    )
    write_graph(graph, tmp_path / "graph", graph_id="cli")
    assert main(["graph-query", str(tmp_path / "graph"), "escalate care"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["hits"]
