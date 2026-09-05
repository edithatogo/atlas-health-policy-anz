from dataclasses import replace
from typing import TypedDict, Unpack

from australian_health_policy_atlas.confidence import compose_confidence
from australian_health_policy_atlas.domain import ConfidenceSignals, EvidenceState


class SignalChanges(TypedDict, total=False):
    provenance_ok: bool
    exact_span_ok: bool
    scope_ok: bool
    authority_ok: bool
    temporal_ok: bool
    deterministic_evidence: bool
    independent_methods_agree: int
    independent_methods_total: int
    benchmark_passed: bool
    coverage: float | None
    conflicting_evidence: bool


def base(**updates: Unpack[SignalChanges]) -> ConfidenceSignals:
    return replace(
        ConfidenceSignals(
            provenance_ok=True,
            exact_span_ok=True,
            scope_ok=True,
            authority_ok=True,
            temporal_ok=True,
        ),
        **updates,
    )


def test_hard_gate_failure_abstains() -> None:
    result = compose_confidence(base(scope_ok=False, deterministic_evidence=True))
    assert result.state is EvidenceState.NOT_DETERMINED


def test_deterministic_evidence_is_a0() -> None:
    assert (
        compose_confidence(base(deterministic_evidence=True)).state
        is EvidenceState.VERIFIED
    )


def test_independent_triangulation_is_a1() -> None:
    result = compose_confidence(
        base(
            independent_methods_agree=3,
            independent_methods_total=3,
            benchmark_passed=True,
            coverage=0.99,
        )
    )
    assert result.state is EvidenceState.HIGH_CONFIDENCE


def test_conflict_cannot_be_upgraded_by_models() -> None:
    result = compose_confidence(
        base(
            independent_methods_agree=4,
            independent_methods_total=4,
            benchmark_passed=True,
            conflicting_evidence=True,
        )
    )
    assert result.state is EvidenceState.PROVISIONAL
