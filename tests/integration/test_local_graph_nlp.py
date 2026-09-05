import json
from pathlib import Path

from australian_health_policy_atlas.local_runner import prepare_local_document


def test_local_preparation_emits_spacy_and_graph(tmp_path: Path) -> None:
    source = tmp_path / "local.txt"
    source.write_text(
        "Registered nurses must escalate clinical deterioration.\n",
        encoding="utf-8",
    )
    output = tmp_path / "out"
    receipt = prepare_local_document(
        source,
        source_id="local",
        output_dir=output,
        use_spacy=True,
        concept_phrases=("clinical deterioration",),
        role_phrases=("Registered nurses",),
        build_graph_projection=True,
    )
    assert receipt["network_used"] is False
    assert receipt["nlp_enabled"] is True
    assert receipt["nlp_row_count"] == 1
    assert receipt["graph_projection"]["authoritative"] is False
    nlp_row = json.loads((output / "nlp-features.jsonl").read_text(encoding="utf-8"))
    labels = {row["label"] for row in nlp_row["spans"]}
    assert "POLICY_CONCEPT" in labels
    nodes = (output / "graph" / "nodes.jsonl").read_text(encoding="utf-8")
    assert "concept:clinical deterioration" in nodes
