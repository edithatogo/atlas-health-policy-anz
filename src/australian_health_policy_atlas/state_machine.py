"""Deterministic finite-state contracts for work items and medallion releases."""

from __future__ import annotations

from dataclasses import dataclass

from .domain import MedallionLayer, ReleaseStatus, WorkStatus


WORK_TRANSITIONS: dict[WorkStatus, frozenset[WorkStatus]] = {
    WorkStatus.QUEUED: frozenset({WorkStatus.EVIDENCE_READY, WorkStatus.FAILED}),
    WorkStatus.EVIDENCE_READY: frozenset({WorkStatus.CANDIDATE, WorkStatus.ABSTAINED, WorkStatus.FAILED}),
    WorkStatus.CANDIDATE: frozenset({WorkStatus.VERIFIED, WorkStatus.SUPPORTED, WorkStatus.PROVISIONAL, WorkStatus.ABSTAINED, WorkStatus.FAILED}),
    WorkStatus.VERIFIED: frozenset(),
    WorkStatus.SUPPORTED: frozenset(),
    WorkStatus.PROVISIONAL: frozenset(),
    WorkStatus.ABSTAINED: frozenset(),
    WorkStatus.FAILED: frozenset(),
}

RELEASE_TRANSITIONS: dict[ReleaseStatus, frozenset[ReleaseStatus]] = {
    ReleaseStatus.PLANNED: frozenset({ReleaseStatus.EXECUTING}),
    ReleaseStatus.EXECUTING: frozenset({ReleaseStatus.CANDIDATE}),
    ReleaseStatus.CANDIDATE: frozenset({ReleaseStatus.EXECUTING, ReleaseStatus.QUALIFIED}),
    ReleaseStatus.QUALIFIED: frozenset({ReleaseStatus.CLOSED}),
    ReleaseStatus.CLOSED: frozenset(),
}

LAYER_PREDECESSOR: dict[MedallionLayer, MedallionLayer | None] = {
    MedallionLayer.CENSUS: None,
    MedallionLayer.BRONZE: MedallionLayer.CENSUS,
    MedallionLayer.SILVER: MedallionLayer.BRONZE,
    MedallionLayer.GOLD: MedallionLayer.SILVER,
    MedallionLayer.PLATINUM: MedallionLayer.GOLD,
    MedallionLayer.GAP_ANALYSIS: MedallionLayer.PLATINUM,
}


class InvalidTransition(ValueError):
    """Raised when a state transition violates the governed workflow."""


def transition_work(current: WorkStatus, target: WorkStatus) -> WorkStatus:
    if target not in WORK_TRANSITIONS[current]:
        raise InvalidTransition(f"work transition {current.value}->{target.value} is not permitted")
    return target


def transition_release(current: ReleaseStatus, target: ReleaseStatus) -> ReleaseStatus:
    if target not in RELEASE_TRANSITIONS[current]:
        raise InvalidTransition(f"release transition {current.value}->{target.value} is not permitted")
    return target


def predecessor_closed(layer: MedallionLayer, closed_layers: set[MedallionLayer]) -> bool:
    predecessor = LAYER_PREDECESSOR[layer]
    return predecessor is None or predecessor in closed_layers


@dataclass(frozen=True, slots=True)
class PromotionDecision:
    permitted: bool
    reasons: tuple[str, ...]


def promotion_gate(
    layer: MedallionLayer,
    *,
    closed_layers: set[MedallionLayer],
    acceptance_results: dict[str, bool],
) -> PromotionDecision:
    reasons: list[str] = []
    if not predecessor_closed(layer, closed_layers):
        reasons.append("predecessor_release_not_closed")
    if not acceptance_results:
        reasons.append("acceptance_evidence_missing")
    failed = sorted(key for key, passed in acceptance_results.items() if passed is not True)
    if failed:
        reasons.extend(f"acceptance_failed:{key}" for key in failed)
    return PromotionDecision(not reasons, tuple(reasons))
