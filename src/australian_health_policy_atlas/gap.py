"""Deterministic gap-matrix construction from pre-qualified assertions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .domain import EvidenceState, PolicyAssertion
from .platinum import baseline_relationship


@dataclass(frozen=True, slots=True)
class GapRow:
    target_assertion_id: str
    comparator_assertion_id: str | None
    relationship: str
    evidence_state: EvidenceState
    reason_codes: tuple[str, ...]


def build_gap_rows(target: Iterable[PolicyAssertion], comparators: Iterable[PolicyAssertion]) -> list[GapRow]:
    comparator_list = list(comparators)
    output: list[GapRow] = []
    for target_assertion in target:
        best: tuple[float, PolicyAssertion] | None = None
        for candidate in comparator_list:
            relationship, state, reasons = baseline_relationship(
                " ".join(filter(None, [target_assertion.actor, target_assertion.action, target_assertion.object, target_assertion.condition, target_assertion.timeframe])),
                " ".join(filter(None, [candidate.actor, candidate.action, candidate.object, candidate.condition, candidate.timeframe])),
                left_modality=target_assertion.modality,
                right_modality=candidate.modality,
                threshold=0.5,
            )
            score = 1.0 if relationship == "candidate_equivalent" else 0.5 if relationship == "material_difference" else 0.0
            if best is None or score > best[0]:
                best = (score, candidate)
                best_result = (relationship, state, reasons)
        if best is None or best[0] == 0.0:
            output.append(GapRow(target_assertion.assertion_id, None, "no_candidate_found", EvidenceState.PROVISIONAL, ("retrieval_coverage_required",)))
        else:
            relationship, state, reasons = best_result
            weakest = max(int(state.value[1]), int(target_assertion.evidence_state.value[1]),
                          int(best[1].evidence_state.value[1]))
            state = EvidenceState(f"A{weakest}")
            if weakest == 4:
                relationship = "not_determined"
            reasons = (*reasons, "confidence_bounded_by_inputs", "comparability_not_qualified")
            output.append(GapRow(target_assertion.assertion_id, best[1].assertion_id, relationship, state, reasons))
    return output
