"""Per-packet progress observations, never authority to promote a medallion layer.

Snapshots detach nested data before checkpointing. Attempted publication without
verified reconstruction has an unknown remote effect, not a claim of zero writes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

from .hashing import canonical_json_bytes, sha256_json
from .integrity import read_json, sealed

if TYPE_CHECKING:
    from .packet_ingestion import PacketSpec


type PacketPhase = Literal[
    "queued",
    "verifying",
    "verified",
    "staging",
    "staged",
    "publishing",
    "published",
    "blocked_missing_hf_token",
    "failed",
]


@dataclass(slots=True)
class PacketProgress:
    """One selected packet and its latest observed execution phase."""

    spec: PacketSpec
    phase: PacketPhase = "queued"
    observation: dict[str, object] | None = None
    publication: dict[str, object] | None = None
    stage_sha256: str | None = None
    network_attempted: bool = False
    failure_phase: PacketPhase | None = None
    error_type: str | None = None

    def as_dict(self) -> dict[str, object]:
        """Project compact progress and links to retained full evidence.

        Returns:
            A progress record; verified existing packages do not imply new writes.

        """
        remote_state = "not_attempted"
        if self.network_attempted:
            remote_state = "unknown"
        if self.publication is not None:
            remote_state = "verified_package_present"
        return {
            "packet_id": self.spec.packet_id,
            "origin": self.spec.as_dict(),
            "phase": self.phase,
            "failure_phase": self.failure_phase,
            "error_type": self.error_type,
            "observation_sha256": (
                self.observation.get("sha256") if self.observation else None
            ),
            "stage_sha256": self.stage_sha256,
            "publication_sha256": (
                self.publication.get("sha256") if self.publication else None
            ),
            "network_attempted": self.network_attempted,
            "remote_write_state": remote_state,
            "remote_bytes_verified": self.publication is not None,
        }


@dataclass(slots=True)
class PacketRun:
    """Finite selection with evidence retained independently for every packet."""

    operation: str
    dataset_id: str
    execution: dict[str, object]
    items: list[PacketProgress] = field(default_factory=list)
    complete: bool = False
    sequence: int = 0

    def status(self) -> str:
        """Distinguish incomplete execution, partial failure and credential absence.

        Returns:
            A run status that never equates a missing credential with publication.

        """
        if not self.complete:
            return "executing"
        failed = sum(item.phase == "failed" for item in self.items)
        if failed:
            return "failed" if failed == len(self.items) else "partial_failure"
        if any(item.phase == "blocked_missing_hf_token" for item in self.items):
            return "blocked_missing_hf_token"
        return "verified"

    def snapshot(self) -> dict[str, object]:
        """Freeze a self-hashed, detached observation of current execution state.

        Returns:
            A new JSON object whose nested values cannot be changed by later work.
            The self-hash supplies fixity, not authentication or semantic truth.

        """
        self.sequence += 1
        publications = [
            item.publication for item in self.items if item.publication is not None
        ]
        attempted = any(item.network_attempted for item in self.items)
        unknown = any(
            item.network_attempted and item.publication is None for item in self.items
        )
        value = sealed({
            "schema_version": "1.1",
            "kind": "registered-source-packet-run",
            "operation": self.operation,
            "status": self.status(),
            "execution_complete": self.complete,
            "checkpoint_sequence": self.sequence,
            "selection_sha256": sha256_json([i.spec.as_dict() for i in self.items]),
            "selected_packet_count": len(self.items),
            "failed_packet_count": sum(i.phase == "failed" for i in self.items),
            "published_packet_count": len(publications),
            "packets": [item.as_dict() for item in self.items],
            "observations": [
                item.observation for item in self.items if item.observation is not None
            ],
            "publication": publications,
            "dataset_id": self.dataset_id,
            "execution": self.execution,
            "network_attempted": attempted,
            "network_used": True if publications else (None if attempted else False),
            "remote_effect_unknown": unknown,
            "remote_bytes_verified": bool(publications),
            "remote_verification_scope": "completed_publication_items_only",
            "all_selected_packets_published": (
                bool(self.items) and len(publications) == len(self.items)
            ),
            "not_medallion_release": True,
            "gate_b_passed": False,
        })
        return read_json(canonical_json_bytes(value))
