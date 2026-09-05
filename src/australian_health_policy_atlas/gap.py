"""Deterministic gap-matrix construction from pre-qualified assertions."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable


from dataclasses import dataclass

from .domain import EvidenceState, PolicyAssertion
from .platinum import baseline_relationship


@dataclass(frozen=True, slots=True)
class GapRow:
    """One reference requirement and its best supported local retrieval candidate."""

    target_assertion_id: str
    comparator_assertion_id: str | None
    relationship: str
    evidence_state: EvidenceState
    reason_codes: tuple[str, ...]


def _assertion_text(assertion: PolicyAssertion) -> str:
    return " ".join(
        item
        for item in (
            assertion.actor,
            assertion.action,
            assertion.object,
            assertion.condition,
            assertion.timeframe,
        )
        if item is not None
    )


@dataclass(frozen=True, slots=True)
class _Candidate:
    score: int
    assertion: PolicyAssertion
    relationship: str
    state: EvidenceState
    reasons: tuple[str, ...]


def _candidate(target: PolicyAssertion, candidate: PolicyAssertion) -> _Candidate:
    relationship, state, reasons = baseline_relationship(
        _assertion_text(target),
        _assertion_text(candidate),
        left_modality=target.modality,
        right_modality=candidate.modality,
        threshold=0.5,
    )
    score = {"candidate_equivalent": 2, "material_difference": 1}.get(relationship, 0)
    return _Candidate(score, candidate, relationship, state, reasons)


def _gap_row(target: PolicyAssertion, match: _Candidate | None) -> GapRow:
    if match is None or match.score == 0:
        return GapRow(
            target.assertion_id,
            None,
            "no_candidate_found",
            EvidenceState.PROVISIONAL,
            ("retrieval_coverage_required",),
        )
    weakest = max(
        int(item.value[1])
        for item in (
            match.state,
            target.evidence_state,
            match.assertion.evidence_state,
        )
    )
    state = EvidenceState(f"A{weakest}")
    relationship = (
        "not_determined"
        if state is EvidenceState.NOT_DETERMINED
        else match.relationship
    )
    return GapRow(
        target.assertion_id,
        match.assertion.assertion_id,
        relationship,
        state,
        (*match.reasons, "confidence_bounded_by_inputs", "comparability_not_qualified"),
    )


def _candidate_score(item: _Candidate) -> int:
    return item.score


def build_gap_rows(
    target: Iterable[PolicyAssertion],
    comparators: Iterable[PolicyAssertion],
) -> list[GapRow]:
    """Return every target's best retrieval candidate without inferring compliance.

    Returns:
        One result for every target assertion, including unresolved retrievals.

    """
    comparator_list = list(comparators)
    return [
        _gap_row(
            assertion,
            max(
                (_candidate(assertion, item) for item in comparator_list),
                key=_candidate_score,
                default=None,
            ),
        )
        for assertion in target
    ]
