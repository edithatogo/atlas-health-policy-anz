"""Rebuildable policy knowledge-graph projection.

The graph is a derived index over medallion records.  It is never authoritative:
all nodes/edges retain identifiers back to Bronze/Silver/Gold/Platinum objects,
and any graph can be deleted and deterministically rebuilt.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from .bronze import BronzeObject
    from .domain import ComparisonFinding, PolicyAssertion
    from .silver import SilverSegment


import json
from dataclasses import dataclass, field
from pathlib import Path

from .hashing import sha256_file, sha256_json
from .records import decode_json, record, string


def _empty_properties() -> dict[str, object]:
    return {}


@dataclass(frozen=True, slots=True)
class GraphNode:
    """Derived evidence entity retaining its original medallion identity."""

    node_id: str
    kind: str
    label: str
    properties: Mapping[str, object] = field(default_factory=_empty_properties)

    def as_dict(self) -> dict[str, object]:
        """Return the record without losing its declared field types.

        Returns:
            A dictionary containing this record's declared fields.

        """
        return {
            "node_id": self.node_id,
            "kind": self.kind,
            "label": self.label,
            "properties": self.properties,
        }


@dataclass(frozen=True, slots=True)
class GraphEdge:
    """Explicit, provenance-bearing relationship between derived graph nodes."""

    source: str
    target: str
    relation: str
    properties: Mapping[str, object] = field(default_factory=_empty_properties)

    def as_dict(self) -> dict[str, object]:
        """Return the record without losing its declared field types.

        Returns:
            A dictionary containing this record's declared fields.

        """
        return {
            "source": self.source,
            "target": self.target,
            "relation": self.relation,
            "properties": self.properties,
        }


@dataclass(slots=True)
class PolicyGraph:
    """Rebuildable evidence graph that cannot promote claims by proximity."""

    nodes: dict[str, GraphNode] = field(default_factory=dict)
    edges: list[GraphEdge] = field(default_factory=list)

    def add_node(self, node: GraphNode) -> None:
        """Register a derived node, rejecting conflicting reuse of its identity.

        Raises:
            ValueError: Graph identities, relationships or retrieval bounds are
            invalid.

        """
        existing = self.nodes.get(node.node_id)
        if existing is not None and existing != node:
            message = f"conflicting graph node: {node.node_id}"
            raise ValueError(message)
        self.nodes[node.node_id] = node

    def add_edge(self, edge: GraphEdge) -> None:
        """Add a relationship only when both endpoint nodes already exist.

        Raises:
            ValueError: Graph identities, relationships or retrieval bounds are
            invalid.

        """
        if edge.source not in self.nodes or edge.target not in self.nodes:
            message = "graph edge endpoints must exist before edge insertion"
            raise ValueError(message)
        if edge not in self.edges:
            self.edges.append(edge)

    def neighbours(self, node_id: str) -> tuple[tuple[GraphEdge, GraphNode], ...]:
        """Return explicit graph neighbours and the edges supporting their traversal.

        Returns:
            Edge and neighbour pairs supporting explicit traversal.

        """
        output: list[tuple[GraphEdge, GraphNode]] = []
        for edge in self.edges:
            if edge.source == node_id:
                output.append((edge, self.nodes[edge.target]))
            elif edge.target == node_id:
                output.append((edge, self.nodes[edge.source]))
        return tuple(output)


def _source_node(source_id: str) -> GraphNode:
    return GraphNode(
        f"source:{source_id}", "source", source_id, {"source_id": source_id}
    )


def build_policy_graph(
    *,
    bronze: Iterable[BronzeObject] = (),
    segments: Iterable[SilverSegment] = (),
    assertions: Iterable[PolicyAssertion] = (),
    findings: Iterable[ComparisonFinding] = (),
    concept_links: Mapping[str, Iterable[str]] | None = None,
    framework_links: Mapping[str, Iterable[str]] | None = None,
) -> PolicyGraph:
    """Build a medallion graph from qualified canonical objects.

    Returns:
        A derived graph preserving supplied input evidence states.

    """
    graph = PolicyGraph()
    _project_bronze(graph, bronze)
    segment_ids = _project_segments(graph, segments)
    assertion_ids = _project_assertions(graph, assertions, segment_ids)
    _project_concepts(graph, concept_links or {}, assertion_ids)
    _project_frameworks(graph, framework_links or {}, assertion_ids)
    _project_findings(graph, findings, assertion_ids)
    return graph


def _project_bronze(graph: PolicyGraph, bronze: Iterable[BronzeObject]) -> None:
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


def _project_segments(
    graph: PolicyGraph, segments: Iterable[SilverSegment]
) -> set[str]:
    segment_ids: set[str] = set()
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

    return segment_ids


def _project_assertions(
    graph: PolicyGraph, assertions: Iterable[PolicyAssertion], segment_ids: set[str]
) -> set[str]:
    assertion_ids: set[str] = set()
    for assertion in assertions:
        assertion_ids.add(assertion.assertion_id)
        source = _source_node(assertion.source_id)
        graph.add_node(source)
        jurisdiction_id = f"jurisdiction:{assertion.jurisdiction}"
        graph.add_node(
            GraphNode(jurisdiction_id, "jurisdiction", assertion.jurisdiction, {})
        )
        node_id = f"assertion:{assertion.assertion_id}"
        label = " ".join(
            filter(
                None,
                [
                    assertion.actor,
                    assertion.modality,
                    assertion.action,
                    assertion.object,
                ],
            )
        )
        graph.add_node(GraphNode(node_id, "assertion", label, assertion.as_dict()))
        graph.add_edge(GraphEdge(source.node_id, node_id, "HAS_ASSERTION"))
        graph.add_edge(GraphEdge(node_id, jurisdiction_id, "APPLIES_IN"))
        if assertion.source_span_id in segment_ids:
            graph.add_edge(
                GraphEdge(f"segment:{assertion.source_span_id}", node_id, "SUPPORTS")
            )

    return assertion_ids


def _project_concepts(
    graph: PolicyGraph,
    concept_links: Mapping[str, Iterable[str]],
    assertion_ids: set[str],
) -> None:
    for assertion_id, concepts in (concept_links or {}).items():
        if assertion_id not in assertion_ids:
            continue
        for concept in concepts:
            canonical = " ".join(concept.strip().lower().split())
            if not canonical:
                continue
            concept_id = f"concept:{canonical}"
            graph.add_node(
                GraphNode(
                    concept_id, "concept", concept.strip(), {"canonical": canonical}
                )
            )
            graph.add_edge(
                GraphEdge(f"assertion:{assertion_id}", concept_id, "MENTIONS_CONCEPT")
            )


def _project_frameworks(
    graph: PolicyGraph,
    framework_links: Mapping[str, Iterable[str]],
    assertion_ids: set[str],
) -> None:
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


def _project_findings(
    graph: PolicyGraph, findings: Iterable[ComparisonFinding], assertion_ids: set[str]
) -> None:
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


def write_graph(
    graph: PolicyGraph, output_dir: str | Path, *, graph_id: str
) -> dict[str, object]:
    """Write deterministic JSONL graph tables and a checksum manifest.

    Returns:
        The result described above, retaining the declared return-type contract.

    """
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
        for edge in sorted(
            graph.edges, key=lambda item: (item.source, item.relation, item.target)
        ):
            handle.write(
                json.dumps(edge.as_dict(), sort_keys=True, ensure_ascii=False) + "\n"
            )
    manifest: dict[str, object] = {
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
    """Load a derived graph and reconstruct its typed nodes and explicit edges.

    Returns:
        The reconstructed, non-authoritative graph projection.

    """
    root = Path(directory)
    graph = PolicyGraph()
    for line in (root / "nodes.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = record(decode_json(line))
            graph.add_node(
                GraphNode(
                    string(row["node_id"]),
                    string(row["kind"]),
                    string(row["label"]),
                    record(row.get("properties", {})),
                )
            )
    for line in (root / "edges.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = record(decode_json(line))
            graph.add_edge(
                GraphEdge(
                    string(row["source"]),
                    string(row["target"]),
                    string(row["relation"]),
                    record(row.get("properties", {})),
                )
            )
    return graph
