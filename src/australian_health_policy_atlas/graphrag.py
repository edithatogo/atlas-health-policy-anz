"""Small-model-friendly GraphRAG retrieval over the derived policy graph."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from .graph import GraphEdge, GraphNode, PolicyGraph


import math
from collections import deque
from dataclasses import dataclass
from typing import TypedDict, Unpack

from .platinum import jaccard_similarity

MAX_GRAPH_HOPS = 8


_RELATION_WEIGHTS: dict[str, float] = {
    "SUPPORTS": 0.28,
    "HAS_ASSERTION": 0.24,
    "MENTIONS_CONCEPT": 0.24,
    "MAPS_TO_FRAMEWORK": 0.24,
    "APPLIES_IN": 0.18,
    "LEFT_OF_COMPARISON": 0.16,
    "RIGHT_OF_COMPARISON": 0.16,
    "CONTAINS": 0.12,
    "CAPTURED_AS": 0.08,
}


@dataclass(frozen=True, slots=True)
class GraphPathStep:
    """A traversed relation retained to explain a retrieved evidence path."""

    source: str
    relation: str
    target: str

    def as_dict(self) -> dict[str, object]:
        """Return the record without losing its declared field types.

        Returns:
            A dictionary containing this record's declared fields.

        """
        return {
            "source": self.source,
            "relation": self.relation,
            "target": self.target,
        }


@dataclass(frozen=True, slots=True)
class GraphRagHit:
    """One retrieved graph node, its score and its supporting traversal path."""

    node_id: str
    kind: str
    label: str
    score: float
    seed_score: float
    hops: int
    path: tuple[GraphPathStep, ...]

    def as_dict(self) -> dict[str, object]:
        """Serialize the declared fields without losing evidence or provenance metadata.

        Returns:
            A dictionary containing this record's declared fields.

        """
        return {
            "node_id": self.node_id,
            "kind": self.kind,
            "label": self.label,
            "score": self.score,
            "seed_score": self.seed_score,
            "hops": self.hops,
            "path": [item.as_dict() for item in self.path],
        }


@dataclass(frozen=True, slots=True)
class GraphRagContext:
    """Bounded retrieval hits and exact evidence segments for a downstream task."""

    query: str
    hits: tuple[GraphRagHit, ...]
    evidence_segments: tuple[GraphNode, ...]
    reason_codes: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        """Serialize the declared fields without losing evidence or provenance metadata.

        Returns:
            A dictionary containing this record's declared fields.

        """
        return {
            "query": self.query,
            "hits": [item.as_dict() for item in self.hits],
            "evidence_segments": [item.as_dict() for item in self.evidence_segments],
            "reason_codes": list(self.reason_codes),
        }


def _node_text(node: GraphNode) -> str:
    values = [node.label]
    for key in (
        "text",
        "actor",
        "modality",
        "action",
        "object",
        "condition",
        "timeframe",
        "authority_type",
    ):
        value = node.properties.get(key)
        if isinstance(value, str):
            values.append(value)
    return " ".join(values)


def _edge_step(current: str, edge: GraphEdge) -> GraphPathStep:
    if edge.source == current:
        return GraphPathStep(edge.source, edge.relation, edge.target)
    return GraphPathStep(edge.target, f"INVERSE_{edge.relation}", edge.source)


class RetrievalOptions(TypedDict, total=False):
    """Finite retrieval settings; external scores remain candidate signals only."""

    top_k: int
    seed_k: int
    max_hops: int
    allowed_kinds: Iterable[str] | None
    external_seed_scores: Mapping[str, float] | None


type PathScore = tuple[float, float, int, tuple[GraphPathStep, ...]]
type Expansion = tuple[str, float, float, int, tuple[GraphPathStep, ...]]


def _seed_nodes(
    graph: PolicyGraph, query: str, options: RetrievalOptions
) -> list[tuple[float, str]]:
    kinds = options.get("allowed_kinds")
    allowed = set(kinds) if kinds is not None else None
    external_scores = options.get("external_seed_scores") or {}
    seeds: list[tuple[float, str]] = []
    for node_id, node in graph.nodes.items():
        if allowed is not None and node.kind not in allowed:
            continue
        external = external_scores.get(node_id, 0.0)
        if not math.isfinite(external) or external < 0:
            message = "external seed scores must be finite and non-negative"
            raise ValueError(message)
        score = max(jaccard_similarity(query, _node_text(node)), external)
        if score > 0:
            seeds.append((score, node_id))
    seeds.sort(key=lambda item: (-item[0], item[1]))
    return seeds[: options.get("seed_k", 6)]


def _expand_paths(
    graph: PolicyGraph, seeds: list[tuple[float, str]], max_hops: int
) -> dict[str, PathScore]:
    best: dict[str, PathScore] = {}
    queue: deque[Expansion] = deque(
        (node_id, score, score, 0, ()) for score, node_id in seeds
    )
    while queue:
        node_id, score, seed_score, hops, path = queue.popleft()
        previous = best.get(node_id)
        if previous is not None and previous[0] >= score:
            continue
        best[node_id] = (score, seed_score, hops, path)
        if hops >= max_hops:
            continue
        for edge, neighbour in graph.neighbours(node_id):
            weight = _RELATION_WEIGHTS.get(edge.relation, 0.08)
            queue.append((
                neighbour.node_id,
                score + weight / (hops + 2),
                seed_score,
                hops + 1,
                (*path, _edge_step(node_id, edge)),
            ))
    return best


def _path_evidence(
    graph: PolicyGraph, hits: tuple[GraphRagHit, ...]
) -> tuple[GraphNode, ...]:
    identities: dict[str, None] = {}
    for hit in hits:
        candidates = [hit.node_id]
        for step in hit.path:
            candidates.extend((step.source, step.target))
        for node_id in candidates:
            node = graph.nodes.get(node_id)
            if node is not None and node.kind == "segment":
                identities[node_id] = None
    return tuple(graph.nodes[node_id] for node_id in identities)


def retrieve_graph_context(
    graph: PolicyGraph, query: str, **options: Unpack[RetrievalOptions]
) -> GraphRagContext:
    """Retrieve candidate seeds and expand finite, source-preserving graph paths.

    External scores select candidates; they cannot promote a claim or establish
    policy equivalence. Each hit retains the exact edges traversed.

    Returns:
        Bounded hits with explicit traversal paths and supporting Silver text.

    Raises:
        TypeError: An input or external return value has an incompatible concrete
        type.
        ValueError: Graph identities, relationships or retrieval bounds are invalid.

    """
    top_k, seed_k, max_hops = (
        options.get("top_k", 12),
        options.get("seed_k", 6),
        options.get("max_hops", 2),
    )
    if type(top_k) is not int or type(seed_k) is not int or type(max_hops) is not int:
        message = "retrieval budgets must be integers"
        raise TypeError(message)
    if top_k <= 0 or seed_k <= 0 or not 0 <= max_hops <= MAX_GRAPH_HOPS:
        message = "positive candidate budgets and zero to eight hops required"
        raise ValueError(message)
    best = _expand_paths(graph, _seed_nodes(graph, query, options), max_hops)
    ordered = sorted(best.items(), key=lambda item: (-item[1][0], item[0]))[:top_k]
    hits = tuple(
        GraphRagHit(
            node_id=node_id,
            kind=graph.nodes[node_id].kind,
            label=graph.nodes[node_id].label,
            score=round(values[0], 6),
            seed_score=round(values[1], 6),
            hops=values[2],
            path=values[3],
        )
        for node_id, values in ordered
    )
    reasons = [
        "derived_graph_non_authoritative",
        "path_preserving_retrieval",
        "external_semantic_seed_scores_supplied"
        if options.get("external_seed_scores")
        else "lexical_seed_only",
    ]
    if not hits:
        reasons.append("no_graph_candidate_found")
    return GraphRagContext(query, hits, _path_evidence(graph, hits), tuple(reasons))
