from pathlib import Path

import pytest

from australian_health_policy_atlas.domain import (
    ComparisonFinding,
    EvidenceState,
    PolicyAssertion,
)
from australian_health_policy_atlas.graph import (
    GraphEdge,
    GraphNode,
    PolicyGraph,
    build_policy_graph,
    load_graph,
    write_graph,
)
from australian_health_policy_atlas.graphrag import retrieve_graph_context
from australian_health_policy_atlas.silver import normalize_text


def _assertion(
    assertion_id: str, segment_id: str, jurisdiction: str, modality: str = "must"
) -> PolicyAssertion:
    return PolicyAssertion(
        assertion_id=assertion_id,
        jurisdiction=jurisdiction,
        source_id="src",
        source_span_id=segment_id,
        actor="registered nurses",
        modality=modality,
        action="escalate",
        object="deteriorating patients",
        evidence_state=EvidenceState.VERIFIED,
    )


def test_policy_graph_build_write_load_and_graphrag(tmp_path: Path) -> None:
    segments = normalize_text(
        "src",
        "Registered nurses must escalate deteriorating patients.\nConsumers may escalate care.",
    )
    left = _assertion("a1", segments[0].segment_id, "QLD")
    right = _assertion("a2", segments[0].segment_id, "NSW")
    finding = ComparisonFinding(
        "f1",
        "a1",
        "a2",
        "candidate_equivalent",
        EvidenceState.HIGH_CONFIDENCE,
        ("triangulated",),
    )
    graph = build_policy_graph(
        segments=segments,
        assertions=[left, right],
        findings=[finding],
        concept_links={
            "a1": ["clinical deterioration"],
            "a2": ["clinical deterioration"],
        },
        framework_links={"a1": ["NSQHS"]},
    )
    assert "concept:clinical deterioration" in graph.nodes
    assert any(edge.relation == "SUPPORTS" for edge in graph.edges)
    manifest = write_graph(graph, tmp_path, graph_id="g1")
    assert manifest["authoritative"] is False
    loaded = load_graph(tmp_path)
    assert loaded.nodes.keys() == graph.nodes.keys()
    context = retrieve_graph_context(loaded, "escalate deteriorating patients")
    assert context.hits
    assert context.evidence_segments
    assert "derived_graph_non_authoritative" in context.reason_codes


def test_graph_rejects_conflicts_and_missing_endpoints() -> None:
    graph = PolicyGraph()
    graph.add_node(GraphNode("x", "concept", "X", {}))
    with pytest.raises(ValueError, match="conflicting graph node"):
        graph.add_node(GraphNode("x", "concept", "Different", {}))
    with pytest.raises(ValueError, match="endpoints"):
        graph.add_edge(GraphEdge("x", "missing", "LINKS"))


def test_graphrag_external_seed_and_no_hits() -> None:
    graph = PolicyGraph()
    graph.add_node(GraphNode("concept:x", "concept", "unrelated", {}))
    context = retrieve_graph_context(
        graph, "zzzz", external_seed_scores={"concept:x": 0.9}
    )
    assert context.hits[0].node_id == "concept:x"
    assert "external_semantic_seed_scores_supplied" in context.reason_codes
    empty = retrieve_graph_context(graph, "zzzz")
    assert not empty.hits
    assert "no_graph_candidate_found" in empty.reason_codes


def test_graph_projects_bronze_frameworks_and_skips_invalid_links(
    tmp_path: Path,
) -> None:
    from australian_health_policy_atlas.bronze import ingest_local_file

    source_file = tmp_path / "policy.txt"
    source_file.write_text("Nurses must escalate care.", encoding="utf-8")
    bronze = ingest_local_file(
        source_file,
        source_id="src",
        source_uri="https://example.test/policy.txt",
        cas_root=tmp_path / "cas",
        observed_at="2026-09-03T00:00:00+00:00",
    )
    segments = normalize_text("src", source_file.read_text(encoding="utf-8"))
    assertion = _assertion("a1", segments[0].segment_id, "QLD")
    dangling = ComparisonFinding(
        "dangling",
        "a1",
        "missing",
        "candidate_equivalent",
        EvidenceState.PROVISIONAL,
        ("missing",),
    )
    graph = build_policy_graph(
        bronze=[bronze],
        segments=segments,
        assertions=[assertion],
        findings=[dangling],
        concept_links={"missing": ["ignored"], "a1": ["", "clinical deterioration"]},
        framework_links={"missing": ["ignored"], "a1": ["", "NSQHS"]},
    )
    assert any(node.kind == "bronze_object" for node in graph.nodes.values())
    assert "framework:nsqhs" in graph.nodes
    assert "concept:clinical deterioration" in graph.nodes
    assert not any(node.kind == "comparison_finding" for node in graph.nodes.values())
    source_neighbours = graph.neighbours("source:src")
    assert source_neighbours
    # Duplicate insertion is idempotent.
    edge = GraphEdge("source:src", "assertion:a1", "HAS_ASSERTION")
    before = len(graph.edges)
    graph.add_edge(edge)
    assert len(graph.edges) == before


def test_load_graph_ignores_blank_lines(tmp_path: Path) -> None:
    (tmp_path / "nodes.jsonl").write_text(
        '{"node_id":"x","kind":"concept","label":"X","properties":{}}\n\n',
        encoding="utf-8",
    )
    (tmp_path / "edges.jsonl").write_text("\n", encoding="utf-8")
    graph = load_graph(tmp_path)
    assert list(graph.nodes) == ["x"]
