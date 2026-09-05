"""Claim-level confidence composition for autonomous reporting."""

from __future__ import annotations

from .domain import ConfidenceResult, ConfidenceSignals, EvidenceState


HARD_GATE_NAMES = ("provenance_ok", "exact_span_ok", "scope_ok", "authority_ok", "temporal_ok")


def compose_confidence(signals: ConfidenceSignals) -> ConfidenceResult:
    failed_hard = [name.removesuffix("_ok") for name in HARD_GATE_NAMES if not getattr(signals, name)]
    if failed_hard:
        return ConfidenceResult(
            EvidenceState.NOT_DETERMINED,
            tuple(f"hard_gate_failed:{name}" for name in failed_hard),
        )
    if signals.conflicting_evidence:
        return ConfidenceResult(EvidenceState.PROVISIONAL, ("conflicting_evidence",))
    if signals.deterministic_evidence:
        return ConfidenceResult(EvidenceState.VERIFIED, ("deterministic_evidence",))
    if (
        signals.independent_methods_total >= 2
        and signals.independent_methods_agree == signals.independent_methods_total
        and signals.benchmark_passed
        and (signals.coverage is None or signals.coverage >= 0.95)
    ):
        return ConfidenceResult(EvidenceState.HIGH_CONFIDENCE, ("independent_triangulation", "benchmark_passed"))
    if signals.benchmark_passed and signals.independent_methods_agree >= 1:
        return ConfidenceResult(EvidenceState.SUPPORTED_NEEDS_VERIFICATION, ("partial_triangulation",))
    return ConfidenceResult(EvidenceState.PROVISIONAL, ("limited_independent_support",))
