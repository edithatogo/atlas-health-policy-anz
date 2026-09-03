"""Offline-first local document preparation and deterministic pre-analysis."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .gold import extract_simple_assertion_fields
from .hashing import sha256_file, sha256_json
from .parsers import parse_file


def prepare_local_document(
    path: str | Path,
    *,
    source_id: str,
    output_dir: str | Path,
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
    for segment in parsed.segments:
        fields = extract_simple_assertion_fields(segment.text)
        if fields.modality is None:
            continue
        gold_rows.append({
            "candidate_id": f"{segment.segment_id}.assertion.1",
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
    with gold_path.open("w", encoding="utf-8") as handle:
        for row in gold_rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    receipt: dict[str, Any] = {
        "schema_version": "1.0",
        "source_id": source_id,
        "input_sha256": sha256_file(source),
        "parser_id": parsed.parser_id,
        "silver_segment_count": len(silver_rows),
        "gold_candidate_count": len(gold_rows),
        "warnings": list(parsed.warnings),
        "network_used": False,
    }
    receipt["receipt_sha256"] = sha256_json(receipt)
    (output / "local-preparation-receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt
