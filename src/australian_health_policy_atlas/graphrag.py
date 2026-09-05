"""Small-model-friendly GraphRAG retrieval over the derived policy graph."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable, Mapping

from .graph import GraphEdge, GraphNode, PolicyGraph
from .platinum import jaccard_similarity


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
    source: str
    relation: str
    target: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class GraphRagHit:
    node_id: str
    kind: str
    label: str
    score: float
    seed_score: float
    hops: int
    path: tuple[GraphPathStep, ...]

    def as_dict(self) -> dict[str, object]:
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
    query: str
    hits: tuple[GraphRagHit, ...]
    evidence_segments: tuple[GraphNode, ...]
    reason_codes: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
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


def _edge_step(current: str, edge: GraphEdge, other: str) -> GraphPathStep:
    if edge.source == current:
        return GraphPathStep(edge.source, edge.relation, edge.target)
    return GraphPathStep(edge.target, f"INVERSE_{edge.relation}", edge.source)


def retrieve_graph_context(
    graph: PolicyGraph,
    query: str,
    *,
    top_k: int = 12,
    seed_k: int = 6,
    max_hops: int = 2,
    allowed_kinds: Iterable[str] | None = None,
    external_seed_scores: Mapping[str, float] | None = None,
) -> GraphRagContext:
    """Retrieve lexical/vector seeds then deterministically expand graph paths.

    ``external_seed_scores`` is the integration point for later qualified
    embeddings/rerankers.  Graph traversal remains deterministic and every hit
    carries its path, so a tiny model receives compact evidence rather than an
    opaque graph summary.
    """
    allowed = set(allowed_kinds) if allowed_kinds is not None else None
    seeds: list[tuple[float, str]] = []
    for node_id, node in graph.nodes.items():
        if allowed is not None and node.kind not in allowed:
            continue
        lexical = jaccard_similarity(query, _node_text(node))
        external = (external_seed_scores or {}).get(node_id, 0.0)
        seed_score = max(lexical, external)
        if seed_score > 0:
            seeds.append((seed_score, node_id))
    seeds.sort(key=lambda item: (-item[0], item[1]))
    seeds = seeds[:seed_k]

    best: dict[str, tuple[float, float, int, tuple[GraphPathStep, ...]]] = {}
    queue: list[tuple[str, float, float, int, tuple[GraphPathStep, ...]]] = []
    for seed_score, node_id in seeds:
        queue.append((node_id, seed_score, seed_score, 0, ()))

    while queue:
        node_id, score, seed_score, hops, path = queue.pop(0)
        previous = best.get(node_id)
        if previous is not None and previous[0] >= score:
            continue
        best[node_id] = (score, seed_score, hops, path)
        if hops >= max_hops:
            continue
        for edge, neighbour in graph.neighbours(node_id):
            relation = edge.relation
            weight = _RELATION_WEIGHTS.get(relation, 0.08)
            next_score = score + weight / (hops + 2)
            step = _edge_step(node_id, edge, neighbour.node_id)
            queue.append((neighbour.node_id, next_score, seed_score, hops + 1, path + (step,)))

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
    evidence_ids: list[str] = []
    for hit in hits:
        if hit.kind == "segment" and hit.node_id not in evidence_ids:
            evidence_ids.append(hit.node_id)
        for step in hit.path:
            for node_id in (step.source, step.target):
                if (
                    node_id in graph.nodes
                    and graph.nodes[node_id].kind == "segment"
                    and node_id not in evidence_ids
                ):
                    evidence_ids.append(node_id)
    evidence = tuple(graph.nodes[node_id] for node_id in evidence_ids)
    reasons = ["derived_graph_non_authoritative", "path_preserving_retrieval"]
    if external_seed_scores:
        reasons.append("external_semantic_seed_scores_supplied")
    else:
        reasons.append("lexical_seed_only")
    if not hits:
        reasons.append("no_graph_candidate_found")
    return GraphRagContext(query, hits, evidence, tuple(reasons))
