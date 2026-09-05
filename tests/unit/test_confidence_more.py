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


def signals(**kwargs: Unpack[SignalChanges]) -> ConfidenceSignals:
    return replace(
        ConfidenceSignals(
            provenance_ok=True,
            exact_span_ok=True,
            scope_ok=True,
            authority_ok=True,
            temporal_ok=True,
        ),
        **kwargs,
    )


def test_a2_partial_triangulation() -> None:
    result = compose_confidence(
        signals(
            benchmark_passed=True,
            independent_methods_agree=1,
            independent_methods_total=2,
        )
    )
    assert result.state is EvidenceState.SUPPORTED_NEEDS_VERIFICATION


def test_a3_limited_support() -> None:
    assert compose_confidence(signals()).state is EvidenceState.PROVISIONAL
