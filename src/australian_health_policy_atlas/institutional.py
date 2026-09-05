"""Institution-owned gap analysis against a pinned public Gold baseline."""

from __future__ import annotations

import json
from pathlib import Path

from .domain import EvidenceState, PolicyAssertion
from .gap import build_gap_rows
from .hashing import sha256_file, sha256_json
from .local_runner import prepare_local_document
from .records import decode_json, optional_string, record, string, strings


def _load_public_assertions(path: str | Path) -> list[PolicyAssertion]:
    output: list[PolicyAssertion] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = record(decode_json(line))
        output.append(
            PolicyAssertion(
                assertion_id=string(row["assertion_id"]),
                jurisdiction=string(row["jurisdiction"]),
                source_id=string(row["source_id"]),
                source_span_id=string(row["source_span_id"]),
                actor=optional_string(row.get("actor")),
                modality=optional_string(row.get("modality")),
                action=optional_string(row.get("action")),
                object=optional_string(row.get("object")),
                condition=optional_string(row.get("condition")),
                timeframe=optional_string(row.get("timeframe")),
                authority_type=optional_string(row.get("authority_type")),
                valid_from=optional_string(row.get("valid_from")),
                valid_to=optional_string(row.get("valid_to")),
                observed_at=optional_string(row.get("observed_at")),
                evidence_state=EvidenceState(string(row.get("evidence_state", "A3"))),
                reason_codes=tuple(strings(row.get("reason_codes", []))),
            )
        )
    return output


def run_institutional_gap_analysis(
    *,
    local_document: str | Path,
    local_source_id: str,
    public_gold_jsonl: str | Path,
    output_dir: str | Path,
) -> dict[str, object]:
    """Compare each baseline requirement with local evidence, in both directions.

    Returns:
        An offline receipt binding baseline and local comparisons to input hashes.

    """
    root = Path(output_dir)
    local_dir = root / "local"
    prepare_local_document(
        local_document, source_id=local_source_id, output_dir=local_dir
    )
    local_assertions: list[PolicyAssertion] = []
    for line in (
        (local_dir / "gold-candidates.jsonl").read_text(encoding="utf-8").splitlines()
    ):
        row = record(decode_json(line))
        local_assertions.append(
            PolicyAssertion(
                assertion_id=string(row["candidate_id"]),
                jurisdiction="INSTITUTION",
                source_id=string(row["source_id"]),
                source_span_id=string(row["source_span_id"]),
                actor=optional_string(row.get("actor")),
                modality=optional_string(row.get("modality")),
                action=optional_string(row.get("action")),
                object=optional_string(row.get("object")),
                timeframe=optional_string(row.get("timeframe")),
                evidence_state=EvidenceState.SUPPORTED_NEEDS_VERIFICATION
                if row.get("deterministic")
                else EvidenceState.PROVISIONAL,
                reason_codes=(string(row.get("reason_code", "unknown")),),
            )
        )
    baseline = _load_public_assertions(public_gold_jsonl)
    # A coverage matrix must visit every reference requirement, not only local clauses.
    rows = build_gap_rows(baseline, local_assertions)
    reverse_rows = build_gap_rows(local_assertions, baseline)
    root.mkdir(parents=True, exist_ok=True)
    matrix_path = root / "gap-matrix.jsonl"
    with matrix_path.open("w", encoding="utf-8") as handle:
        for gap_row in rows:
            handle.write(
                json.dumps(
                    {
                        "reference_assertion_id": gap_row.target_assertion_id,
                        "local_candidate_assertion_id": gap_row.comparator_assertion_id,
                        "target_assertion_id": gap_row.target_assertion_id,
                        "comparator_assertion_id": gap_row.comparator_assertion_id,
                        "relationship": gap_row.relationship,
                        "evidence_state": gap_row.evidence_state.value,
                        "reason_codes": list(gap_row.reason_codes),
                    },
                    sort_keys=True,
                )
                + "\n"
            )
    with (root / "local-to-reference-candidates.jsonl").open(
        "w", encoding="utf-8"
    ) as handle:
        for gap_row in reverse_rows:
            handle.write(
                json.dumps(
                    {
                        "local_assertion_id": gap_row.target_assertion_id,
                        "reference_candidate_assertion_id": (
                            gap_row.comparator_assertion_id
                        ),
                        "relationship": gap_row.relationship,
                        "evidence_state": gap_row.evidence_state.value,
                        "reason_codes": list(gap_row.reason_codes),
                    },
                    sort_keys=True,
                )
                + "\n"
            )
    receipt: dict[str, object] = {
        "schema_version": "1.0",
        "local_document_sha256": sha256_file(local_document),
        "public_gold_sha256": sha256_file(public_gold_jsonl),
        "local_assertions": len(local_assertions),
        "public_assertions": len(baseline),
        "gap_rows": len(rows),
        "direction": "reference_requirements_against_local_corpus",
        "coverage_denominator": "reference_assertion_count",
        "matrix_sha256": sha256_file(matrix_path),
        "reverse_matrix_sha256": sha256_file(
            root / "local-to-reference-candidates.jsonl"
        ),
        "network_used": False,
        "limitations": [
            (
                "no_candidate_found is a retrieval result, not "
                "confirmed policy non-compliance"
            ),
            (
                "deterministic simple-clause extraction only "
                "unless a qualified model/parser is added"
            ),
            (
                "baseline lexical matching is candidate-level and "
                "must not be treated as semantic equivalence "
                "without Platinum evidence"
            ),
        ],
    }
    receipt["receipt_sha256"] = sha256_json(receipt)
    (root / "institutional-gap-receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return receipt
