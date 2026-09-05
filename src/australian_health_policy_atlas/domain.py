"""Typed domain objects and evidence states."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class EvidenceState(StrEnum):
    """Claim-level evidence states; model agreement is not ground truth."""

    VERIFIED = "A0"
    HIGH_CONFIDENCE = "A1"
    SUPPORTED_NEEDS_VERIFICATION = "A2"
    PROVISIONAL = "A3"
    NOT_DETERMINED = "A4"


class MedallionLayer(StrEnum):
    """Ordered data products with independently qualified promotion prerequisites."""

    CENSUS = "census"
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    GAP_ANALYSIS = "gap-analysis"


class ReleaseStatus(StrEnum):
    """Finite release lifecycle states, distinct from individual claim confidence."""

    PLANNED = "planned"
    EXECUTING = "executing"
    CANDIDATE = "candidate"
    QUALIFIED = "qualified"
    CLOSED = "closed"


class WorkStatus(StrEnum):
    """Lifecycle of a bounded work item, including terminal failure or abstention."""

    QUEUED = "queued"
    EVIDENCE_READY = "evidence_ready"
    CANDIDATE = "candidate"
    VERIFIED = "verified"
    SUPPORTED = "supported"
    PROVISIONAL = "provisional"
    ABSTAINED = "abstained"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class EvidenceSpan:
    """Exact source text and offsets used to ground an assertion or model packet."""

    source_id: str
    span_id: str
    text: str
    sha256: str
    context_role: str = "primary"

    def as_dict(self) -> dict[str, object]:
        """Return the record without losing its declared field types.

        Returns:
            A dictionary containing this record's declared fields.

        """
        return {
            "source_id": self.source_id,
            "span_id": self.span_id,
            "text": self.text,
            "sha256": self.sha256,
            "context_role": self.context_role,
        }


@dataclass(frozen=True, slots=True)
class PolicyAssertion:
    """Typed policy proposition with source anchors and explicit uncertainty."""

    assertion_id: str
    jurisdiction: str
    source_id: str
    source_span_id: str
    actor: str | None
    modality: str | None
    action: str | None
    object: str | None
    condition: str | None = None
    timeframe: str | None = None
    authority_type: str | None = None
    valid_from: str | None = None
    valid_to: str | None = None
    observed_at: str | None = None
    evidence_state: EvidenceState = EvidenceState.PROVISIONAL
    reason_codes: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, object]:
        """Return the record without losing its declared field types.

        Returns:
            A dictionary containing this record's declared fields.

        """
        return {
            "assertion_id": self.assertion_id,
            "jurisdiction": self.jurisdiction,
            "source_id": self.source_id,
            "source_span_id": self.source_span_id,
            "actor": self.actor,
            "modality": self.modality,
            "action": self.action,
            "object": self.object,
            "condition": self.condition,
            "timeframe": self.timeframe,
            "authority_type": self.authority_type,
            "valid_from": self.valid_from,
            "valid_to": self.valid_to,
            "observed_at": self.observed_at,
            "evidence_state": self.evidence_state.value,
            "reason_codes": self.reason_codes,
        }


@dataclass(frozen=True, slots=True)
class ComparisonFinding:
    """Pairwise policy comparison retaining evidence state and diagnostic reasons."""

    finding_id: str
    left_assertion_id: str
    right_assertion_id: str
    relationship: str
    evidence_state: EvidenceState
    reason_codes: tuple[str, ...]
    method_evidence: tuple[str, ...] = field(default_factory=tuple)
    coverage: float | None = None

    def as_dict(self) -> dict[str, object]:
        """Return the record without losing its declared field types.

        Returns:
            A dictionary containing this record's declared fields.

        """
        return {
            "finding_id": self.finding_id,
            "left_assertion_id": self.left_assertion_id,
            "right_assertion_id": self.right_assertion_id,
            "relationship": self.relationship,
            "evidence_state": self.evidence_state.value,
            "reason_codes": self.reason_codes,
            "method_evidence": self.method_evidence,
            "coverage": self.coverage,
        }


@dataclass(frozen=True, slots=True)
class ConfidenceSignals:
    """Independent evidence dimensions supplied to the confidence composer."""

    provenance_ok: bool
    exact_span_ok: bool
    scope_ok: bool
    authority_ok: bool
    temporal_ok: bool
    deterministic_evidence: bool = False
    independent_methods_agree: int = 0
    independent_methods_total: int = 0
    benchmark_passed: bool = False
    coverage: float | None = None
    conflicting_evidence: bool = False


@dataclass(frozen=True, slots=True)
class ConfidenceResult:
    """Composed evidence state and the reasons determining that state."""

    state: EvidenceState
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ReleaseReceipt:
    """Immutable release decision bound to scope, inputs and acceptance evidence."""

    release_id: str
    layer: MedallionLayer
    status: ReleaseStatus
    input_manifest_sha256: str
    output_manifest_sha256: str
    acceptance_results: dict[str, bool]
    evidence_state: EvidenceState
    reason_codes: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        """Return the record without losing its declared field types.

        Returns:
            A dictionary containing this record's declared fields.

        """
        return {
            "release_id": self.release_id,
            "layer": self.layer.value,
            "status": self.status.value,
            "input_manifest_sha256": self.input_manifest_sha256,
            "output_manifest_sha256": self.output_manifest_sha256,
            "acceptance_results": self.acceptance_results,
            "evidence_state": self.evidence_state.value,
            "reason_codes": self.reason_codes,
        }
