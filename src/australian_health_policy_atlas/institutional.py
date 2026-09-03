"""Institution-owned gap analysis against a pinned public Gold baseline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .domain import EvidenceState, PolicyAssertion
from .gap import build_gap_rows
from .hashing import sha256_file, sha256_json
from .local_runner import prepare_local_document


def _load_public_assertions(path: str | Path) -> list[PolicyAssertion]:
    output: list[PolicyAssertion] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        output.append(
            PolicyAssertion(
                assertion_id=row["assertion_id"],
                jurisdiction=row["jurisdiction"],
                source_id=row["source_id"],
                source_span_id=row["source_span_id"],
                actor=row.get("actor"),
                modality=row.get("modality"),
                action=row.get("action"),
                object=row.get("object"),
                condition=row.get("condition"),
                timeframe=row.get("timeframe"),
                authority_type=row.get("authority_type"),
                valid_from=row.get("valid_from"),
                valid_to=row.get("valid_to"),
                observed_at=row.get("observed_at"),
                evidence_state=EvidenceState(row.get("evidence_state", "A3")),
                reason_codes=tuple(row.get("reason_codes", [])),
            )
        )
    return output


def run_institutional_gap_analysis(
    *,
    local_document: str | Path,
    local_source_id: str,
    public_gold_jsonl: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    root = Path(output_dir)
    local_dir = root / "local"
    prep = prepare_local_document(local_document, source_id=local_source_id, output_dir=local_dir)
    local_assertions: list[PolicyAssertion] = []
    for line in (local_dir / "gold-candidates.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        local_assertions.append(
            PolicyAssertion(
                assertion_id=row["candidate_id"],
                jurisdiction="INSTITUTION",
                source_id=row["source_id"],
                source_span_id=row["source_span_id"],
                actor=row.get("actor"),
                modality=row.get("modality"),
                action=row.get("action"),
                object=row.get("object"),
                timeframe=row.get("timeframe"),
                evidence_state=EvidenceState.VERIFIED if row.get("deterministic") else EvidenceState.PROVISIONAL,
                reason_codes=(row.get("reason_code", "unknown"),),
            )
        )
    baseline = _load_public_assertions(public_gold_jsonl)
    rows = build_gap_rows(local_assertions, baseline)
    root.mkdir(parents=True, exist_ok=True)
    matrix_path = root / "gap-matrix.jsonl"
    with matrix_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps({
                "target_assertion_id": row.target_assertion_id,
                "comparator_assertion_id": row.comparator_assertion_id,
                "relationship": row.relationship,
                "evidence_state": row.evidence_state.value,
                "reason_codes": list(row.reason_codes),
            }, sort_keys=True) + "\n")
    receipt: dict[str, Any] = {
        "schema_version": "1.0",
        "local_document_sha256": sha256_file(local_document),
        "public_gold_sha256": sha256_file(public_gold_jsonl),
        "local_assertions": len(local_assertions),
        "public_assertions": len(baseline),
        "gap_rows": len(rows),
        "network_used": False,
        "limitations": [
            "deterministic simple-clause extraction only unless a qualified model/parser is added",
            "baseline lexical matching is candidate-level and must not be treated as semantic equivalence without Platinum evidence",
        ],
    }
    receipt["receipt_sha256"] = sha256_json(receipt)
    (root / "institutional-gap-receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt
