"""Deterministic finite-state contracts for work items and medallion releases."""

from __future__ import annotations

from dataclasses import dataclass

from .domain import MedallionLayer, ReleaseStatus, WorkStatus

WORK_TRANSITIONS: dict[WorkStatus, frozenset[WorkStatus]] = {
    WorkStatus.QUEUED: frozenset({WorkStatus.EVIDENCE_READY, WorkStatus.FAILED}),
    WorkStatus.EVIDENCE_READY: frozenset({
        WorkStatus.CANDIDATE,
        WorkStatus.ABSTAINED,
        WorkStatus.FAILED,
    }),
    WorkStatus.CANDIDATE: frozenset({
        WorkStatus.VERIFIED,
        WorkStatus.SUPPORTED,
        WorkStatus.PROVISIONAL,
        WorkStatus.ABSTAINED,
        WorkStatus.FAILED,
    }),
    WorkStatus.VERIFIED: frozenset(),
    WorkStatus.SUPPORTED: frozenset(),
    WorkStatus.PROVISIONAL: frozenset(),
    WorkStatus.ABSTAINED: frozenset(),
    WorkStatus.FAILED: frozenset(),
}

RELEASE_TRANSITIONS: dict[ReleaseStatus, frozenset[ReleaseStatus]] = {
    ReleaseStatus.PLANNED: frozenset({ReleaseStatus.EXECUTING}),
    ReleaseStatus.EXECUTING: frozenset({ReleaseStatus.CANDIDATE}),
    ReleaseStatus.CANDIDATE: frozenset({
        ReleaseStatus.EXECUTING,
        ReleaseStatus.QUALIFIED,
    }),
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


class InvalidTransitionError(ValueError):
    """Raised when a state transition violates the governed workflow."""


# Compatibility name retained for existing clients and recorded trace readers.
InvalidTransition = InvalidTransitionError


def transition_work(current: WorkStatus, target: WorkStatus) -> WorkStatus:
    """Apply a permitted finite work-item transition or reject the request.

    Returns:
        The requested work state when the transition is permitted.

    Raises:
        InvalidTransitionError: The requested transition is not permitted by the
        lifecycle contract.

    """
    if target not in WORK_TRANSITIONS[current]:
        message = f"work transition {current.value}->{target.value} is not permitted"
        raise InvalidTransitionError(message)
    return target


def transition_release(current: ReleaseStatus, target: ReleaseStatus) -> ReleaseStatus:
    """Apply a permitted release transition without reopening a closed lifecycle.

    Returns:
        The requested release state when the transition is permitted.

    Raises:
        InvalidTransitionError: The requested transition is not permitted by the
        lifecycle contract.

    """
    if target not in RELEASE_TRANSITIONS[current]:
        message = f"release transition {current.value}->{target.value} is not permitted"
        raise InvalidTransitionError(message)
    return target


def predecessor_closed(
    layer: MedallionLayer, closed_layers: set[MedallionLayer]
) -> bool:
    """Check whether the immediately preceding medallion layer is closed.

    Returns:
        True for the first layer or when its predecessor is in closed_layers.

    """
    predecessor = LAYER_PREDECESSOR[layer]
    return predecessor is None or predecessor in closed_layers


@dataclass(frozen=True, slots=True)
class PromotionDecision:
    """Non-compensatory promotion decision and unmet acceptance reasons."""

    permitted: bool
    reasons: tuple[str, ...]


def promotion_gate(
    layer: MedallionLayer,
    *,
    closed_layers: set[MedallionLayer],
    acceptance_results: dict[str, bool],
) -> PromotionDecision:
    """Require closed prerequisites and explicit true acceptance evidence for promotion.

    Returns:
        The promotion decision with all unmet reasons retained.

    """
    reasons: list[str] = []
    if not predecessor_closed(layer, closed_layers):
        reasons.append("predecessor_release_not_closed")
    if not acceptance_results:
        reasons.append("acceptance_evidence_missing")
    failed = sorted(
        key for key, passed in acceptance_results.items() if passed is not True
    )
    if failed:
        reasons.extend(f"acceptance_failed:{key}" for key in failed)
    return PromotionDecision(not reasons, tuple(reasons))
