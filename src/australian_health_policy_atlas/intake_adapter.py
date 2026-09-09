"""Lossless-evidence adapter for the earlier finite original-document intake.

Only capture metadata is projected. Raw request/manifest bytes stay pinned and
are retained in staging; no observation, document text or policy meaning is made up.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from .integrity import REVISION
from .records import integer, record, records, string

if TYPE_CHECKING:
    from .packet_ingestion import PacketSpec

FIELDS = {
    "source_id": "id",
    "title": "title",
    "url": "url",
    "licence": "rights",
    "attribution": "attribution",
    "rights_basis": "rights_evidence",
}
MAXIMUM_SOURCES = 256
MAXIMUM_BYTES = 256 * 1024 * 1024
MAXIMUM_OBJECT_BYTES = 32 * 1024 * 1024


def _require(condition: object, message: str) -> None:
    if condition is not True:
        raise ValueError(message)


def _header(
    request: dict[str, object], capture: dict[str, object], spec: PacketSpec
) -> None:
    for document in (request, capture):
        _require(integer(document["schema_version"]) == 1, "unsupported intake schema")
        _require(
            document["collection_id"] == spec.packet_id, "intake identity mismatch"
        )
        _require(document.get("medallion_promotion") is False, "intake cannot promote")
    _require(
        request.get("kind") == "bounded-original-public-document-intake",
        "unsupported intake kind",
    )
    _require(
        request.get("evaluation_material_allowed") is False
        and capture.get("evaluation_material") is False,
        "evaluation material is not a public source packet",
    )
    _require(
        capture["request_sha256"] == spec.request_sha256, "intake request pin mismatch"
    )
    _require(
        bool(REVISION.fullmatch(string(capture["code_revision"]))),
        "invalid capture revision",
    )
    _require(
        datetime.fromisoformat(string(capture["captured_at"])).utcoffset() is not None,
        "intake completion time needs a timezone",
    )


def _source(row: dict[str, object]) -> dict[str, object]:
    return {target: string(row[source]) for target, source in FIELDS.items()}


def _captured(row: dict[str, object], spec: PacketSpec) -> dict[str, object]:
    _require(
        row.get("original_unmodified") is True
        and row.get("semantic_qualification") is False,
        "unqualified unchanged original required",
    )
    receipt = record(row["receipt"])
    _require(receipt["requested_url"] == row["url"], "intake requested URL mismatch")
    path = string(receipt["stored_path"])
    prefix = spec.directory + "/"
    _require(
        path.startswith(prefix + "originals/"), "intake original outside its collection"
    )
    return {
        **_source(row),
        **{
            key: receipt[key]
            for key in (
                "observed_at",
                "http_status",
                "final_url",
                "sha256",
                "size_bytes",
                "media_type",
                "etag",
                "last_modified",
            )
        },
        "stored_path": path.removeprefix(prefix),
        "status": "captured_original",
        "parsing_qualified": False,
        # The common verifier ALWAYS checks header/EOF and exact original bytes.
        # This projection is not a claim of an additional historical capture check.
        "pdf_signature_checked": True,
    }


def _outcome(
    row: dict[str, object], capture: dict[str, object], spec: PacketSpec
) -> dict[str, object]:
    _require(
        row.get("remote_verification") is False,
        "capture snapshot cannot claim publication",
    )
    if row["status"] == "captured_original_pdf":
        return _captured(row, spec)
    _require(row["status"] == "capture_failed", "unknown intake status")
    _require(
        row.get("receipt") is None, "failed intake must not carry an original receipt"
    )
    return {
        **_source(row),
        "observed_at": capture["captured_at"],
        "observed_at_basis": "batch_completion_not_individual_request_time",
        "status": "capture_failed",
        "parsing_qualified": False,
        "error": string(row["error"]),
        "error_type": string(row["error_type"]),
    }


def _budgets(
    request: dict[str, object],
    capture: dict[str, object],
    outcomes: list[dict[str, object]],
) -> None:
    maximum = integer(request["maximum_documents"])
    per_object = integer(request["maximum_bytes_per_document"])
    total = integer(request["maximum_total_bytes"])
    _require(0 < maximum <= MAXIMUM_SOURCES, "invalid intake source budget")
    _require(0 < per_object <= MAXIMUM_OBJECT_BYTES, "invalid intake object budget")
    _require(0 < total <= MAXIMUM_BYTES, "invalid intake byte budget")
    _require(
        len(records(request["sources"]))
        == len(outcomes)
        == integer(capture["requested_count"])
        and len(outcomes) <= maximum,
        "intake requested count mismatch",
    )
    sizes = [
        integer(row["size_bytes"])
        for row in outcomes
        if row["status"] == "captured_original"
    ]
    _require(
        all(0 < size <= per_object for size in sizes), "intake object exceeds budget"
    )
    _require(
        sum(sizes) == integer(capture["bytes"]) and sum(sizes) <= total,
        "intake byte count mismatch",
    )
    _require(
        len(sizes) == integer(capture["captured_count"]),
        "intake captured count mismatch",
    )


def project_intake(
    request: dict[str, object], capture: dict[str, object], spec: PacketSpec
) -> tuple[dict[str, object], dict[str, object]]:
    """Adapt pinned original metadata to the shared packet verification interface.

    Returns:
        Transient metadata projections. Original JSON bytes, notices and dates
        remain the evidence. Failure timestamps are explicitly batch-level only.
        The common verifier still checks membership, provenance and every PDF byte.

    """
    _header(request, capture, spec)
    sources = [_source(row) for row in records(request["sources"])]
    outcomes = [_outcome(row, capture, spec) for row in records(capture["records"])]
    _budgets(request, capture, outcomes)
    return {"packet_id": spec.packet_id, "sources": sources}, {
        "schema_version": "source-packet-1.0",
        "packet_id": spec.packet_id,
        "qualification": "source_staging_only_not_bronze_closure",
        "evaluation_included": False,
        "hugging_face_write": False,
        "source_count": capture["requested_count"],
        "captured_count": capture["captured_count"],
        "objects": outcomes,
    }
