"""Offline-first local document preparation and deterministic pre-analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from .silver import SilverSegment


import json
from pathlib import Path
from typing import TypedDict, Unpack

from .domain import EvidenceState, PolicyAssertion
from .gold import extract_simple_assertion_fields
from .graph import build_policy_graph, write_graph
from .hashing import sha256_file, sha256_json
from .nlp import analyse_with_spacy
from .parsers import parse_file


class LocalOptions(TypedDict, total=False):
    """Optional local projections, never implied publication or qualification."""

    use_spacy: bool
    spacy_model: str | None
    concept_phrases: tuple[str, ...]
    role_phrases: tuple[str, ...]
    build_graph_projection: bool


def _write_jsonl(path: Path, rows: Iterable[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _local_assertion(
    source_id: str, segment: SilverSegment
) -> tuple[dict[str, object], PolicyAssertion] | None:
    fields = extract_simple_assertion_fields(segment.text)
    if fields.modality is None:
        return None
    candidate_id = f"{segment.segment_id}.assertion.1"
    state = (
        EvidenceState.SUPPORTED_NEEDS_VERIFICATION
        if fields.deterministic
        else EvidenceState.PROVISIONAL
    )
    row: dict[str, object] = {
        "candidate_id": candidate_id,
        "source_id": source_id,
        "source_span_id": segment.segment_id,
        "source_text_sha256": segment.text_sha256,
        "actor": fields.actor,
        "modality": fields.modality,
        "action": fields.action,
        "object": fields.object,
        "timeframe": fields.timeframe,
        "deterministic": fields.deterministic,
        "reason_code": fields.reason_code,
        "evidence_state": state.value,
    }
    assertion = PolicyAssertion(
        assertion_id=candidate_id,
        jurisdiction="INSTITUTION",
        source_id=source_id,
        source_span_id=segment.segment_id,
        actor=fields.actor,
        modality=fields.modality,
        action=fields.action,
        object=fields.object,
        timeframe=fields.timeframe,
        evidence_state=state,
        reason_codes=(fields.reason_code, "extractor_not_qualified"),
    )
    return row, assertion


def _local_nlp(
    segments: tuple[SilverSegment, ...],
    assertions: list[PolicyAssertion],
    options: LocalOptions,
) -> tuple[list[dict[str, object]], dict[str, list[str]]]:
    rows: list[dict[str, object]] = []
    links: dict[str, list[str]] = {}
    identities = {item.assertion_id for item in assertions}
    for segment in segments:
        analysis = analyse_with_spacy(
            segment.text,
            model_name=options.get("spacy_model"),
            concept_phrases=options.get("concept_phrases", ()),
            role_phrases=options.get("role_phrases", ()),
        )
        rows.append({"segment_id": segment.segment_id, **analysis.as_dict()})
        concepts = [
            span.text for span in analysis.spans if span.label == "POLICY_CONCEPT"
        ]
        assertion_id = f"{segment.segment_id}.assertion.1"
        if concepts and assertion_id in identities:
            links[assertion_id] = concepts
    return rows, links


def prepare_local_document(
    path: str | Path,
    *,
    source_id: str,
    output_dir: str | Path,
    **options: Unpack[LocalOptions],
) -> dict[str, object]:
    """Prepare local Silver segments and unqualified Gold/NLP/graph projections.

    Returns:
        An offline preparation receipt whose candidate claims remain unqualified.

    """
    source, output = Path(path), Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    parsed = parse_file(source, source_id=source_id)
    _write_jsonl(
        output / "silver.jsonl", [segment.as_dict() for segment in parsed.segments]
    )
    candidates = [
        item
        for segment in parsed.segments
        if (item := _local_assertion(source_id, segment)) is not None
    ]
    _write_jsonl(output / "gold-candidates.jsonl", [item[0] for item in candidates])
    assertions = [item[1] for item in candidates]
    nlp_rows, concept_links = (
        _local_nlp(parsed.segments, assertions, options)
        if options.get("use_spacy")
        else ([], {})
    )
    if options.get("use_spacy"):
        _write_jsonl(output / "nlp-features.jsonl", nlp_rows)
    graph_manifest = None
    if options.get("build_graph_projection"):
        graph = build_policy_graph(
            segments=parsed.segments, assertions=assertions, concept_links=concept_links
        )
        graph_manifest = write_graph(
            graph, output / "graph", graph_id=f"{source_id}.local"
        )
    receipt: dict[str, object] = {
        "schema_version": "1.0",
        "source_id": source_id,
        "input_sha256": sha256_file(source),
        "parser_id": parsed.parser_id,
        "silver_segment_count": len(parsed.segments),
        "gold_candidate_count": len(candidates),
        "warnings": list(parsed.warnings),
        "nlp_enabled": options.get("use_spacy", False),
        "nlp_row_count": len(nlp_rows),
        "spacy_model": options.get("spacy_model"),
        "graph_projection": graph_manifest,
        "network_used": False,
    }
    receipt["receipt_sha256"] = sha256_json(receipt)
    (output / "local-preparation-receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return receipt
