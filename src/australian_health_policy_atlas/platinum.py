"""Transparent baseline comparison primitives for Platinum qualification."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .domain import EvidenceState


_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokens(text: str) -> frozenset[str]:
    return frozenset(_TOKEN_RE.findall(text.lower()))


def jaccard_similarity(left: str, right: str) -> float:
    a, b = tokens(left), tokens(right)
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


@dataclass(frozen=True, slots=True)
class Comparability:
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
    similarity = jaccard_similarity(left_text, right_text)
    if similarity < threshold:
        return "not_equivalent", EvidenceState.SUPPORTED_NEEDS_VERIFICATION, ("lexical_similarity_below_threshold",)
    if left_modality and right_modality and left_modality != right_modality:
        return "material_difference", EvidenceState.VERIFIED, ("modality_mismatch",)
    return "candidate_equivalent", EvidenceState.SUPPORTED_NEEDS_VERIFICATION, ("lexical_candidate_only",)
