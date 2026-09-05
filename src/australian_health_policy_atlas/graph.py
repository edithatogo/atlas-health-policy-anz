"""Rebuildable policy knowledge-graph projection.

The graph is a derived index over medallion records.  It is never authoritative:
all nodes/edges retain identifiers back to Bronze/Silver/Gold/Platinum objects,
and any graph can be deleted and deterministically rebuilt.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from .bronze import BronzeObject
from .domain import ComparisonFinding, PolicyAssertion
from .hashing import sha256_file, sha256_json
from .silver import SilverSegment


@dataclass(frozen=True, slots=True)
class GraphNode:
    node_id: str
    kind: str
    label: str
    properties: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class GraphEdge:
    source: str
    target: str
    relation: str
    properties: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PolicyGraph:
    nodes: dict[str, GraphNode] = field(default_factory=dict)
    edges: list[GraphEdge] = field(default_factory=list)

    def add_node(self, node: GraphNode) -> None:
        existing = self.nodes.get(node.node_id)
        if existing is not None and existing != node:
            raise ValueError(f"conflicting graph node: {node.node_id}")
        self.nodes[node.node_id] = node

    def add_edge(self, edge: GraphEdge) -> None:
        if edge.source not in self.nodes or edge.target not in self.nodes:
            raise ValueError("graph edge endpoints must exist before edge insertion")
        if edge not in self.edges:
            self.edges.append(edge)

    def neighbours(self, node_id: str) -> tuple[tuple[GraphEdge, GraphNode], ...]:
        output: list[tuple[GraphEdge, GraphNode]] = []
        for edge in self.edges:
            if edge.source == node_id:
                output.append((edge, self.nodes[edge.target]))
            elif edge.target == node_id:
                output.append((edge, self.nodes[edge.source]))
        return tuple(output)


def _source_node(source_id: str) -> GraphNode:
    return GraphNode(f"source:{source_id}", "source", source_id, {"source_id": source_id})


def build_policy_graph(
    *,
    bronze: Iterable[BronzeObject] = (),
    segments: Iterable[SilverSegment] = (),
    assertions: Iterable[PolicyAssertion] = (),
    findings: Iterable[ComparisonFinding] = (),
    concept_links: Mapping[str, Iterable[str]] | None = None,
    framework_links: Mapping[str, Iterable[str]] | None = None,
) -> PolicyGraph:
    """Build a medallion graph from qualified canonical objects."""
    graph = PolicyGraph()
    segment_ids: set[str] = set()

    for item in bronze:
        source = _source_node(item.source_id)
        graph.add_node(source)
        object_id = f"object:{item.object_id}"
        graph.add_node(
            GraphNode(
                object_id,
                "bronze_object",
                item.source_id,
                {
                    "object_id": item.object_id,
                    "sha256": item.sha256,
                    "source_uri": item.source_uri,
                    "media_type": item.media_type,
                    "observed_at": item.observed_at,
                },
            )
        )
        graph.add_edge(GraphEdge(source.node_id, object_id, "CAPTURED_AS"))

    for segment in segments:
        source = _source_node(segment.source_id)
        graph.add_node(source)
        node_id = f"segment:{segment.segment_id}"
        segment_ids.add(segment.segment_id)
        graph.add_node(
            GraphNode(
                node_id,
                "segment",
                segment.text[:160],
                {
                    "segment_id": segment.segment_id,
                    "source_id": segment.source_id,
                    "text": segment.text,
                    "text_sha256": segment.text_sha256,
                    "locator": segment.locator,
                    "parser_id": segment.parser_id,
                },
            )
        )
        graph.add_edge(GraphEdge(source.node_id, node_id, "CONTAINS"))

    assertion_ids: set[str] = set()
    for assertion in assertions:
        assertion_ids.add(assertion.assertion_id)
        source = _source_node(assertion.source_id)
        graph.add_node(source)
        jurisdiction_id = f"jurisdiction:{assertion.jurisdiction}"
        graph.add_node(GraphNode(jurisdiction_id, "jurisdiction", assertion.jurisdiction, {}))
        node_id = f"assertion:{assertion.assertion_id}"
        label = " ".join(
            filter(
                None,
                [assertion.actor, assertion.modality, assertion.action, assertion.object],
            )
        )
        graph.add_node(GraphNode(node_id, "assertion", label, assertion.as_dict()))
        graph.add_edge(GraphEdge(source.node_id, node_id, "HAS_ASSERTION"))
        graph.add_edge(GraphEdge(node_id, jurisdiction_id, "APPLIES_IN"))
        if assertion.source_span_id in segment_ids:
            graph.add_edge(GraphEdge(f"segment:{assertion.source_span_id}", node_id, "SUPPORTS"))

    for assertion_id, concepts in (concept_links or {}).items():
        if assertion_id not in assertion_ids:
            continue
        for concept in concepts:
            canonical = " ".join(concept.strip().lower().split())
            if not canonical:
                continue
            concept_id = f"concept:{canonical}"
            graph.add_node(
                GraphNode(concept_id, "concept", concept.strip(), {"canonical": canonical})
            )
            graph.add_edge(GraphEdge(f"assertion:{assertion_id}", concept_id, "MENTIONS_CONCEPT"))

    for assertion_id, frameworks in (framework_links or {}).items():
        if assertion_id not in assertion_ids:
            continue
        for framework in frameworks:
            canonical = " ".join(framework.strip().lower().split())
            if not canonical:
                continue
            framework_id = f"framework:{canonical}"
            graph.add_node(
                GraphNode(
                    framework_id,
                    "framework",
                    framework.strip(),
                    {"canonical": canonical},
                )
            )
            graph.add_edge(
                GraphEdge(
                    f"assertion:{assertion_id}",
                    framework_id,
                    "MAPS_TO_FRAMEWORK",
                )
            )

    for finding in findings:
        if (
            finding.left_assertion_id not in assertion_ids
            or finding.right_assertion_id not in assertion_ids
        ):
            continue
        finding_id = f"finding:{finding.finding_id}"
        graph.add_node(
            GraphNode(
                finding_id,
                "comparison_finding",
                finding.relationship,
                finding.as_dict(),
            )
        )
        graph.add_edge(
            GraphEdge(
                f"assertion:{finding.left_assertion_id}",
                finding_id,
                "LEFT_OF_COMPARISON",
            )
        )
        graph.add_edge(
            GraphEdge(
                finding_id,
                f"assertion:{finding.right_assertion_id}",
                "RIGHT_OF_COMPARISON",
            )
        )
    return graph


def write_graph(graph: PolicyGraph, output_dir: str | Path, *, graph_id: str) -> dict[str, Any]:
    """Write deterministic JSONL graph tables and a checksum manifest."""
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    nodes_path = root / "nodes.jsonl"
    edges_path = root / "edges.jsonl"
    with nodes_path.open("w", encoding="utf-8") as handle:
        for node_id in sorted(graph.nodes):
            handle.write(
                json.dumps(
                    graph.nodes[node_id].as_dict(),
                    sort_keys=True,
                    ensure_ascii=False,
                )
                + "\n"
            )
    with edges_path.open("w", encoding="utf-8") as handle:
        for edge in sorted(graph.edges, key=lambda item: (item.source, item.relation, item.target)):
            handle.write(json.dumps(edge.as_dict(), sort_keys=True, ensure_ascii=False) + "\n")
    manifest: dict[str, Any] = {
        "schema_version": "1.0",
        "graph_id": graph_id,
        "authoritative": False,
        "rebuildable_projection": True,
        "node_count": len(graph.nodes),
        "edge_count": len(graph.edges),
        "nodes_sha256": sha256_file(nodes_path),
        "edges_sha256": sha256_file(edges_path),
    }
    manifest["manifest_sha256"] = sha256_json(manifest)
    (root / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def load_graph(directory: str | Path) -> PolicyGraph:
    root = Path(directory)
    graph = PolicyGraph()
    for line in (root / "nodes.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            graph.add_node(
                GraphNode(
                    row["node_id"],
                    row["kind"],
                    row["label"],
                    row.get("properties", {}),
                )
            )
    for line in (root / "edges.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            graph.add_edge(
                GraphEdge(
                    row["source"],
                    row["target"],
                    row["relation"],
                    row.get("properties", {}),
                )
            )
    return graph
