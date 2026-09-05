"""Transparent baseline comparison primitives for Platinum qualification."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .domain import EvidenceState

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokens(text: str) -> frozenset[str]:
    """Normalise a string into the lexical token set used for candidate retrieval.

    Returns:
        The unique normalised tokens used by the lexical baseline.

    """
    return frozenset(match.group(0) for match in _TOKEN_RE.finditer(text.lower()))


def jaccard_similarity(left: str, right: str) -> float:
    """Measure token-set overlap as a retrieval signal, not semantic equivalence.

    Returns:
        Token-set intersection over union, with two empty sets scoring one.

    """
    a, b = tokens(left), tokens(right)
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


@dataclass(frozen=True, slots=True)
class Comparability:
    """Hard-gate result for scope, time and authority comparability."""

    comparable: bool
    reasons: tuple[str, ...]


def qualify_comparability(
    *,
    left_scope: str | None,
    right_scope: str | None,
    left_authority: str | None,
    right_authority: str | None,
    left_valid: bool,
    right_valid: bool,
) -> Comparability:
    """Check independent scope, authority and temporal gates before comparison.

    Returns:
        Whether all hard gates pass and the failed gate names.

    """
    reasons: list[str] = []
    if not left_valid or not right_valid:
        reasons.append("temporal_mismatch")
    if not left_scope or not right_scope:
        reasons.append("scope_unclear")
    if not left_authority or not right_authority:
        reasons.append("authority_unclear")
    return Comparability(not reasons, tuple(reasons))


def baseline_relationship(
    left_text: str,
    right_text: str,
    *,
    left_modality: str | None,
    right_modality: str | None,
    threshold: float = 0.72,
) -> tuple[str, EvidenceState, tuple[str, ...]]:
    """Generate a lexical candidate, not a qualified equivalence judgment.

    Returns:
        A candidate relationship, evidence state and reasons; not a compliance
        verdict.

    Raises:
        ValueError: The supplied data violates the function's documented validation
        contract.

    """
    if not 0 <= threshold <= 1:
        message = "threshold must be between zero and one"
        raise ValueError(message)
    if not left_text.strip() or not right_text.strip():
        return "not_determined", EvidenceState.NOT_DETERMINED, ("evidence_missing",)
    similarity = jaccard_similarity(left_text, right_text)
    if similarity < threshold:
        return (
            "not_determined",
            EvidenceState.NOT_DETERMINED,
            ("lexical_nonmatch_is_not_semantic_non_equivalence",),
        )
    if left_modality and right_modality and left_modality != right_modality:
        return (
            "material_difference",
            EvidenceState.SUPPORTED_NEEDS_VERIFICATION,
            ("modality_mismatch", "lexical_context_not_qualified"),
        )
    return (
        "candidate_equivalent",
        EvidenceState.SUPPORTED_NEEDS_VERIFICATION,
        ("lexical_candidate_only",),
    )
