"""Typed domain objects and evidence states."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class EvidenceState(StrEnum):
    VERIFIED = "A0"
    HIGH_CONFIDENCE = "A1"
    SUPPORTED_NEEDS_VERIFICATION = "A2"
    PROVISIONAL = "A3"
    NOT_DETERMINED = "A4"


class MedallionLayer(StrEnum):
    CENSUS = "census"
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    GAP_ANALYSIS = "gap-analysis"


class ReleaseStatus(StrEnum):
    PLANNED = "planned"
    EXECUTING = "executing"
    CANDIDATE = "candidate"
    QUALIFIED = "qualified"
    CLOSED = "closed"


class WorkStatus(StrEnum):
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
    source_id: str
    span_id: str
    text: str
    sha256: str
    context_role: str = "primary"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PolicyAssertion:
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

    def as_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["evidence_state"] = self.evidence_state.value
        return value


@dataclass(frozen=True, slots=True)
class ComparisonFinding:
    finding_id: str
    left_assertion_id: str
    right_assertion_id: str
    relationship: str
    evidence_state: EvidenceState
    reason_codes: tuple[str, ...]
    method_evidence: tuple[str, ...] = field(default_factory=tuple)
    coverage: float | None = None

    def as_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["evidence_state"] = self.evidence_state.value
        return value


@dataclass(frozen=True, slots=True)
class ConfidenceSignals:
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
    state: EvidenceState
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ReleaseReceipt:
    release_id: str
    layer: MedallionLayer
    status: ReleaseStatus
    input_manifest_sha256: str
    output_manifest_sha256: str
    acceptance_results: dict[str, bool]
    evidence_state: EvidenceState
    reason_codes: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["layer"] = self.layer.value
        value["status"] = self.status.value
        value["evidence_state"] = self.evidence_state.value
        return value
