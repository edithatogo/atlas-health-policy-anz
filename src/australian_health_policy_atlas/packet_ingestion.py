"""Verify finite original-document packets without manufacturing crawl or release state.

Registry pins are independent of the packet's self-reported hashes. Verification
is offline: source authority, currency and policy semantics are not inferred.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

from dataclasses import dataclass
from datetime import datetime
from http import HTTPStatus
from typing import Literal
from urllib.parse import urlsplit

from .hashing import sha256_bytes, sha256_file
from .integrity import IDENTIFIER, REVISION, SHA256, read_json, safe_path, sealed
from .records import integer, records, string, strings

MAX_METADATA_BYTES = 1024 * 1024
MAX_OBJECT_BYTES = 32 * 1024 * 1024
MAX_PACKET_BYTES = 256 * 1024 * 1024
MAX_SOURCES = 256
PDF_TAIL_BYTES = 65536
ASCII_SPACE = 32
SOURCE_FIELDS = ("source_id", "title", "url", "licence", "attribution", "rights_basis")
Layout = Literal["original", "staged"]


def require_packet(condition: object, message: str) -> None:
    """Reject any unmet packet integrity condition.

    Raises:
        ValueError: The packet violates its declared input or integrity contract.

    """
    if condition is not True:
        raise ValueError(message)


@dataclass(frozen=True, slots=True)
class PacketSpec:
    """Independently pinned original metadata and the explicitly unresolved census."""

    packet_id: str
    directory: str
    source_revision: str
    request_sha256: str
    capture_sha256: str
    allowed_hosts: tuple[str, ...]
    known_census_gaps: tuple[str, ...]

    @classmethod
    def from_record(cls, value: dict[str, object]) -> PacketSpec:
        """Validate a registry entry, without accepting coercions or mutable revisions.

        Returns:
            The validated, immutable packet specification.

        """
        result = cls(
            packet_id=string(value["packet_id"]),
            directory=string(value["directory"]),
            source_revision=string(value["source_revision"]),
            request_sha256=string(value["request_sha256"]),
            capture_sha256=string(value["capture_sha256"]),
            allowed_hosts=tuple(strings(value["allowed_hosts"])),
            known_census_gaps=tuple(strings(value["known_census_gaps"])),
        )
        result.validate()
        return result

    def validate(self) -> None:
        """Require canonical identities, a packet-only directory and unique hosts."""
        require_packet(bool(IDENTIFIER.fullmatch(self.packet_id)), "invalid packet ID")
        require_packet(
            self.directory == f"source-packets/{self.packet_id}",
            "packet directory does not match identity",
        )
        require_packet(
            bool(REVISION.fullmatch(self.source_revision)), "mutable source revision"
        )
        for digest in (self.request_sha256, self.capture_sha256):
            require_packet(bool(SHA256.fullmatch(digest)), "invalid metadata hash")
        require_packet(
            bool(self.allowed_hosts)
            and len(set(self.allowed_hosts)) == len(self.allowed_hosts),
            "nonempty unique source hosts required",
        )
        for host in self.allowed_hosts:
            require_packet(
                urlsplit(f"https://{host}").netloc == host
                and urlsplit(f"https://{host}").hostname == host
                and all(c.isascii() and (c.isalnum() or c in ".-") for c in host),
                "invalid declared host",
            )
        require_packet(
            all(self.known_census_gaps)
            and len(set(self.known_census_gaps)) == len(self.known_census_gaps),
            "invalid census gaps",
        )

    def as_dict(self) -> dict[str, object]:
        """Serialize the explicit publication identity, with no local absolute paths.

        Returns:
            A JSON-compatible record of this independently pinned specification.

        """
        return {
            "packet_id": self.packet_id,
            "directory": self.directory,
            "source_revision": self.source_revision,
            "request_sha256": self.request_sha256,
            "capture_sha256": self.capture_sha256,
            "allowed_hosts": list(self.allowed_hosts),
            "known_census_gaps": list(self.known_census_gaps),
        }


def load_packet_registry(repository: Path) -> list[PacketSpec]:
    """Read the governed packet allowlist, rejecting duplicate or empty membership.

    Returns:
        Validated packet specifications; this is not a new policy-source census.

    """
    path = safe_path(repository, "data/sources/source-packets-v1.json")
    value = read_json(_bounded_bytes(path, MAX_METADATA_BYTES))
    require_packet(
        type(value.get("schema_version")) is int and value["schema_version"] == 1,
        "unsupported packet registry",
    )
    specs = [PacketSpec.from_record(row) for row in records(value["packets"])]
    require_packet(0 < len(specs) <= MAX_SOURCES, "invalid packet registry size")
    require_packet(
        len({s.packet_id for s in specs}) == len(specs), "duplicate packet ID"
    )
    return specs


def _bounded_bytes(path: Path, maximum: int) -> bytes:
    require_packet(
        path.is_file() and not path.is_symlink(), "regular source file required"
    )
    require_packet(0 < path.stat().st_size <= maximum, "source size exceeds budget")
    with path.open("rb") as stream:
        data = stream.read(maximum + 1)
    require_packet(0 < len(data) <= maximum, "source grew beyond budget")
    return data


def _pinned_json(root: Path, name: str, digest: str) -> dict[str, object]:
    data = _bounded_bytes(safe_path(root, name), MAX_METADATA_BYTES)
    require_packet(sha256_bytes(data) == digest, "pinned metadata changed: " + name)
    return read_json(data)


def _url(url: str, spec: PacketSpec) -> None:
    parts = urlsplit(url)
    require_packet(
        parts.scheme == "https"
        and parts.hostname in spec.allowed_hosts
        and not parts.username
        and not parts.password
        and parts.port in {None, 443}
        and not parts.fragment
        and not any(c.isspace() or ord(c) < ASCII_SPACE for c in url),
        "source URL outside declared HTTPS scope",
    )


def _members(value: object) -> dict[str, dict[str, object]]:
    rows = records(value)
    require_packet(0 < len(rows) <= MAX_SOURCES, "invalid source count")
    indexed: dict[str, dict[str, object]] = {}
    for row in rows:
        source_id = string(row["source_id"])
        require_packet(bool(IDENTIFIER.fullmatch(source_id)), "invalid source ID")
        require_packet(source_id not in indexed, "duplicate source ID")
        indexed[source_id] = row
    return indexed


def _metadata(
    root: Path, spec: PacketSpec, layout: Layout
) -> tuple[
    dict[str, dict[str, object]], dict[str, dict[str, object]], dict[str, object]
]:
    prefix = "evidence/" if layout == "staged" else ""
    request = _pinned_json(root, prefix + "request.json", spec.request_sha256)
    capture = _pinned_json(root, prefix + "capture-manifest.json", spec.capture_sha256)
    require_packet(
        request["packet_id"] == capture["packet_id"] == spec.packet_id,
        "metadata packet identity mismatch",
    )
    require_packet(
        capture.get("schema_version") == "source-packet-1.0",
        "unsupported capture schema",
    )
    require_packet(
        capture.get("qualification") == "source_staging_only_not_bronze_closure",
        "packet cannot assert medallion qualification",
    )
    require_packet(
        capture.get("evaluation_included") is False,
        "sensitive evaluation content cannot enter public packet staging",
    )
    require_packet(
        capture.get("hugging_face_write") is False,
        "capture receipt cannot substitute for remote publication",
    )
    requested, captured = _members(request["sources"]), _members(capture["objects"])
    require_packet(
        requested.keys() == captured.keys(), "request/capture membership mismatch"
    )
    require_packet(
        integer(capture["source_count"]) == len(requested), "wrong source count"
    )
    return requested, captured, capture


def _record_metadata(
    row: dict[str, object], expected: dict[str, object], spec: PacketSpec
) -> None:
    for field in SOURCE_FIELDS:
        require_packet(
            bool(string(row[field])) and row[field] == expected[field],
            "source provenance mismatch: " + field,
        )
    _url(string(row["url"]), spec)
    observed = datetime.fromisoformat(string(row["observed_at"]))
    require_packet(
        observed.utcoffset() is not None, "observation needs an explicit timezone"
    )
    require_packet(
        row.get("parsing_qualified") is False, "parsing qualification not supported"
    )
    if row.get("final_url") is not None:
        _url(string(row["final_url"]), spec)


def _pdf(path: Path, row: dict[str, object]) -> None:
    require_packet(
        path.is_file() and not path.is_symlink(), "regular original required"
    )
    size = integer(row["size_bytes"])
    require_packet(
        0 < size <= MAX_OBJECT_BYTES and path.stat().st_size == size,
        "original size mismatch or budget exceeded",
    )
    require_packet(sha256_file(path) == row["sha256"], "original hash mismatch")
    with path.open("rb") as stream:
        require_packet(stream.read(5) == b"%PDF-", "original PDF signature missing")
        stream.seek(max(0, size - PDF_TAIL_BYTES))
        require_packet(
            b"%%EOF" in stream.read(PDF_TAIL_BYTES), "original PDF end marker missing"
        )


def _captured(root: Path, row: dict[str, object], layout: Layout) -> dict[str, object]:
    digest = string(row["sha256"])
    require_packet(bool(SHA256.fullmatch(digest)), "invalid original hash")
    original = string(row["stored_path"])
    require_packet(
        original.startswith("originals/") and original.endswith(".pdf"),
        "original outside packet inventory",
    )
    safe_path(root, original)
    require_packet(
        integer(row["http_status"]) == HTTPStatus.OK, "original not an HTTP 200 capture"
    )
    require_packet(
        row.get("pdf_signature_checked") is True, "missing transport signature check"
    )
    require_packet(
        row.get("media_type") in {"application/pdf", "application/octet-stream"},
        "invalid captured media type",
    )
    require_packet(bool(string(row["final_url"])), "final capture URL missing")
    relative = f"objects/{digest}.pdf" if layout == "staged" else original
    _pdf(safe_path(root, relative), row)
    return {
        **{
            k: row[k]
            for k in (
                *SOURCE_FIELDS,
                "observed_at",
                "final_url",
                "media_type",
                "size_bytes",
            )
        },
        "sha256": digest,
        "object_id": "sha256:" + digest,
        "dataset_path": f"objects/{digest}.pdf",
        "original_path": original,
        "parsing_qualified": False,
    }


def _failure(row: dict[str, object]) -> dict[str, object]:
    require_packet(
        row["status"] in {"capture_failed", "rights_pending"}, "unknown capture status"
    )
    require_packet(
        all(row.get(k) is None for k in ("sha256", "size_bytes", "stored_path")),
        "failed capture must not carry an original object",
    )
    require_packet(bool(string(row["error"])), "failed capture has no recorded reason")
    return dict(row)


def inventory_paths(root: Path) -> set[str]:
    """Enumerate regular files, rejecting symlinks and non-file filesystem members.

    Returns:
        Canonical relative paths; no network access or implicit file selection.

    """
    require_packet(
        root.is_dir() and not root.is_symlink(), "regular directory required"
    )
    result: set[str] = set()
    for path in root.rglob("*"):
        require_packet(not path.is_symlink(), "symlinks are not permitted in a packet")
        if not path.is_dir():
            require_packet(path.is_file(), "non-regular packet member")
            name = path.relative_to(root).as_posix()
            safe_path(root, name)
            result.add(name)
    return result


def inspect_packet(
    root: Path, spec: PacketSpec, *, layout: Layout = "original"
) -> dict[str, object]:
    """Verify pinned metadata, exact membership and every captured original offline.

    Returns:
        A deterministic, self-hashed integrity observation. Failures and census
        gaps remain explicit; the returned observation never passes Bronze Gate B.

    """
    spec.validate()
    require_packet(layout in {"original", "staged"}, "unsupported packet layout")
    requested, captured, manifest = _metadata(root, spec, layout)
    require_packet(
        sum(
            integer(row["size_bytes"])
            for row in captured.values()
            if row["status"] == "captured_original"
        )
        <= MAX_PACKET_BYTES,
        "packet byte budget exceeded before original reads",
    )
    objects: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    for source_id, row in sorted(captured.items()):
        _record_metadata(row, requested[source_id], spec)
        if row["status"] == "captured_original":
            objects.append(_captured(root, row, layout))
        else:
            failures.append(_failure(row))
    require_packet(
        integer(manifest["captured_count"]) == len(objects), "wrong captured count"
    )
    original_paths = [string(row["original_path"]) for row in objects]
    require_packet(
        len(set(original_paths)) == len(original_paths), "duplicate original path"
    )
    unique = {string(row["sha256"]): integer(row["size_bytes"]) for row in objects}
    require_packet(
        sum(unique.values()) <= MAX_PACKET_BYTES, "packet byte budget exceeded"
    )
    directory = "objects" if layout == "staged" else "originals"
    expected = {
        string(row["dataset_path"] if layout == "staged" else row["original_path"])
        for row in objects
    }
    object_root = safe_path(root, directory)
    actual: set[str] = (
        {directory + "/" + p for p in inventory_paths(object_root)}
        if object_root.exists()
        else set()
    )
    require_packet(actual == expected, "original file inventory mismatch")
    return sealed({
        "schema_version": "1.0",
        "kind": "packet-integrity-observation",
        "origin": spec.as_dict(),
        "source_count": len(requested),
        "captured_count": len(objects),
        "failed_count": len(failures),
        "unique_object_count": len(unique),
        "total_unique_bytes": sum(unique.values()),
        "requested_source_ids": sorted(requested),
        "objects": objects,
        "capture_failures": failures,
        "known_census_gaps": list(spec.known_census_gaps),
        "integrity_verified": True,
        "network_used": False,
        "acquisition_complete": not failures and not spec.known_census_gaps,
        "not_medallion_release": True,
        "gate_b_passed": False,
    })
