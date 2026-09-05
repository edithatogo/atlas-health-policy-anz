from australian_health_policy_atlas.confidence import compose_confidence
from australian_health_policy_atlas.domain import ConfidenceSignals, EvidenceState


def signals(**kwargs: object) -> ConfidenceSignals:
    base = dict(provenance_ok=True, exact_span_ok=True, scope_ok=True, authority_ok=True, temporal_ok=True)
    base.update(kwargs)
    return ConfidenceSignals(**base)  # type: ignore[arg-type]


def test_a2_partial_triangulation() -> None:
    result = compose_confidence(signals(benchmark_passed=True, independent_methods_agree=1, independent_methods_total=2))
    assert result.state is EvidenceState.SUPPORTED_NEEDS_VERIFICATION


def test_a3_limited_support() -> None:
    assert compose_confidence(signals()).state is EvidenceState.PROVISIONAL
