"""Offline-first local document preparation and deterministic pre-analysis."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .domain import EvidenceState, PolicyAssertion
from .gold import extract_simple_assertion_fields
from .graph import build_policy_graph, write_graph
from .hashing import sha256_file, sha256_json
from .nlp import analyse_with_spacy
from .parsers import parse_file


def prepare_local_document(
    path: str | Path,
    *,
    source_id: str,
    output_dir: str | Path,
    use_spacy: bool = False,
    spacy_model: str | None = None,
    concept_phrases: tuple[str, ...] = (),
    role_phrases: tuple[str, ...] = (),
    build_graph_projection: bool = False,
) -> dict[str, Any]:
    """Create local Silver segments and deterministic Gold candidates without network use."""
    source = Path(path)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    parsed = parse_file(source, source_id=source_id)
    silver_path = output / "silver.jsonl"
    gold_path = output / "gold-candidates.jsonl"
    silver_rows = [segment.as_dict() for segment in parsed.segments]
    with silver_path.open("w", encoding="utf-8") as handle:
        for row in silver_rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    gold_rows: list[dict[str, Any]] = []
    typed_assertions: list[PolicyAssertion] = []
    nlp_rows: list[dict[str, Any]] = []
    concept_links: dict[str, list[str]] = {}
    for segment in parsed.segments:
        fields = extract_simple_assertion_fields(segment.text)
        if fields.modality is None:
            continue
        candidate_id = f"{segment.segment_id}.assertion.1"
        gold_rows.append({
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
        })
        typed_assertions.append(PolicyAssertion(
            assertion_id=candidate_id,
            jurisdiction="INSTITUTION",
            source_id=source_id,
            source_span_id=segment.segment_id,
            actor=fields.actor,
            modality=fields.modality,
            action=fields.action,
            object=fields.object,
            timeframe=fields.timeframe,
            evidence_state=(
                EvidenceState.VERIFIED
                if fields.deterministic
                else EvidenceState.PROVISIONAL
            ),
            reason_codes=(fields.reason_code,),
        ))
    with gold_path.open("w", encoding="utf-8") as handle:
        for row in gold_rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    if use_spacy:
        for segment in parsed.segments:
            analysis = analyse_with_spacy(
                segment.text,
                model_name=spacy_model,
                concept_phrases=concept_phrases,
                role_phrases=role_phrases,
            )
            row = {"segment_id": segment.segment_id, **analysis.as_dict()}
            nlp_rows.append(row)
            concepts = [span.text for span in analysis.spans if span.label == "POLICY_CONCEPT"]
            if concepts:
                assertion_id = f"{segment.segment_id}.assertion.1"
                if any(item.assertion_id == assertion_id for item in typed_assertions):
                    concept_links[assertion_id] = concepts
        nlp_path = output / "nlp-features.jsonl"
        with nlp_path.open("w", encoding="utf-8") as handle:
            for row in nlp_rows:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    graph_manifest: dict[str, Any] | None = None
    if build_graph_projection:
        graph = build_policy_graph(
            segments=parsed.segments,
            assertions=typed_assertions,
            concept_links=concept_links,
        )
        graph_manifest = write_graph(graph, output / "graph", graph_id=f"{source_id}.local")
    receipt: dict[str, Any] = {
        "schema_version": "1.0",
        "source_id": source_id,
        "input_sha256": sha256_file(source),
        "parser_id": parsed.parser_id,
        "silver_segment_count": len(silver_rows),
        "gold_candidate_count": len(gold_rows),
        "warnings": list(parsed.warnings),
        "nlp_enabled": use_spacy,
        "nlp_row_count": len(nlp_rows),
        "spacy_model": spacy_model,
        "graph_projection": graph_manifest,
        "network_used": False,
    }
    receipt["receipt_sha256"] = sha256_json(receipt)
    (output / "local-preparation-receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return receipt
