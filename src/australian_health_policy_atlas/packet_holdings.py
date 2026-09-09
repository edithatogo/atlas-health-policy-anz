"""Byte-level holdings across verified packets, without collapsing source histories."""

from __future__ import annotations

from .integrity import SHA256, sealed, verify_seal
from .packet_ingestion import require_packet
from .records import integer, record, records, string


def summarize_holdings(observations: list[dict[str, object]]) -> dict[str, object]:
    """Count exact original bytes once while retaining all source observations.

    Returns:
        A deterministic summary scoped only to the verified input observations.
        Byte identity does not establish policy identity, currency or equivalence.
        Capture failures are never resolved by another packet's successful capture.
        Call only after source verification; a sealed observation is not a signature.

    """
    unique: dict[str, int] = {}
    identifiers: set[str] = set()
    occurrences = requested = failed = 0
    for observation in observations:
        verify_seal(observation)
        require_packet(
            observation.get("integrity_verified") is True, "unverified holdings input"
        )
        identity = string(record(observation["origin"])["packet_id"])
        require_packet(identity not in identifiers, "duplicate holdings packet")
        identifiers.add(identity)
        objects = records(observation["objects"])
        failures = records(observation["capture_failures"])
        require_packet(
            integer(observation["captured_count"]) == len(objects)
            and integer(observation["failed_count"]) == len(failures)
            and integer(observation["source_count"]) == len(objects) + len(failures),
            "holdings source counts disagree",
        )
        requested += len(objects) + len(failures)
        failed += len(failures)
        for row in objects:
            digest, size = string(row["sha256"]), integer(row["size_bytes"])
            require_packet(
                bool(SHA256.fullmatch(digest)) and size > 0, "invalid holdings object"
            )
            require_packet(
                digest not in unique or unique[digest] == size,
                "inconsistent duplicate object size",
            )
            unique[digest] = size
            occurrences += 1
    return sealed({
        "schema_version": "1.0",
        "kind": "verified-packet-byte-holdings",
        "scope": "successfully_verified_packet_observations_only",
        "verified_packet_count": len(identifiers),
        "packet_ids": sorted(identifiers),
        "requested_source_record_count": requested,
        "captured_original_occurrences": occurrences,
        "failed_capture_record_count": failed,
        "unique_original_count": len(unique),
        "unique_original_bytes": sum(unique.values()),
        "repeated_original_occurrences": occurrences - len(unique),
        "object_identities": [
            {"sha256": key, "size_bytes": unique[key]} for key in sorted(unique)
        ],
        "policy_equivalence_inferred": False,
        "historical_failures_resolved": False,
        "not_medallion_release": True,
        "gate_b_passed": False,
    })
