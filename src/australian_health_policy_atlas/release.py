"""Finite release qualification and receipts."""

from __future__ import annotations

from .confidence import compose_confidence
from .domain import (
    ConfidenceSignals,
    EvidenceState,
    MedallionLayer,
    ReleaseReceipt,
    ReleaseStatus,
)
from .hashing import sha256_json
from .state_machine import promotion_gate


def qualify_release(
    *,
    release_id: str,
    layer: MedallionLayer,
    input_manifest: dict[str, object],
    output_manifest: dict[str, object],
    acceptance_results: dict[str, bool],
    closed_layers: set[MedallionLayer],
) -> ReleaseReceipt:
    gate = promotion_gate(
        layer, closed_layers=closed_layers, acceptance_results=acceptance_results
    )
    if not gate.permitted:
        return ReleaseReceipt(
            release_id=release_id,
            layer=layer,
            status=ReleaseStatus.CANDIDATE,
            input_manifest_sha256=sha256_json(input_manifest),
            output_manifest_sha256=sha256_json(output_manifest),
            acceptance_results=acceptance_results,
            evidence_state=EvidenceState.NOT_DETERMINED,
            reason_codes=gate.reasons,
        )
    confidence = compose_confidence(
        ConfidenceSignals(
            provenance_ok=True,
            exact_span_ok=True,
            scope_ok=True,
            authority_ok=True,
            temporal_ok=True,
            deterministic_evidence=True,
        )
    )
    return ReleaseReceipt(
        release_id=release_id,
        layer=layer,
        status=ReleaseStatus.QUALIFIED,
        input_manifest_sha256=sha256_json(input_manifest),
        output_manifest_sha256=sha256_json(output_manifest),
        acceptance_results=acceptance_results,
        evidence_state=confidence.state,
        reason_codes=confidence.reason_codes,
    )
