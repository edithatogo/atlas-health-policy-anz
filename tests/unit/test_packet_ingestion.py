"""Pinning, membership, provenance and byte rejection tests."""

from __future__ import annotations

import os
from dataclasses import replace
from typing import TYPE_CHECKING

import pytest

from australian_health_policy_atlas.hashing import sha256_bytes
from australian_health_policy_atlas.integrity import atomic_json, verify_seal
from australian_health_policy_atlas.packet_ingestion import (
    MAX_PACKET_BYTES,
    PacketSpec,
    inspect_packet,
    inventory_paths,
    load_packet_registry,
)
from australian_health_policy_atlas.records import records
from tests.packet_support import PDF, packet_fixture

if TYPE_CHECKING:
    from pathlib import Path


def test_exact_packet_retains_failure_and_census(tmp_path: Path) -> None:
    fixture = packet_fixture(tmp_path)
    result = inspect_packet(fixture.root, fixture.spec)
    verify_seal(result)
    assert result["captured_count"] == result["failed_count"] == 1
    assert result["source_count"] == 2
    assert result["total_unique_bytes"] == len(PDF)
    assert result["known_census_gaps"] == ["Unlocated report"]
    assert result["integrity_verified"]
    assert not result["network_used"]
    assert not result["acquisition_complete"]
    assert not result["gate_b_passed"]
    assert load_packet_registry(fixture.registry()) == [fixture.spec]
    assert PacketSpec.from_record(fixture.spec.as_dict()) == fixture.spec


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("packet_id", "other"),
        ("schema_version", "unknown"),
        ("qualification", "bronze-complete"),
        ("evaluation_included", True),
        ("hugging_face_write", True),
        ("source_count", True),
        ("source_count", 3),
        ("captured_count", 2),
    ],
)
def test_pinned_but_invalid_manifest_rejected(
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    fixture = packet_fixture(tmp_path)
    fixture.manifest[field] = value
    with pytest.raises((ValueError, TypeError)):
        inspect_packet(fixture.root, fixture.pin())


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source_id", "../alpha"),
        ("title", "Different"),
        ("observed_at", "2026-09-10T00:00:00"),
        ("parsing_qualified", True),
        ("final_url", "https://evil.invalid/stolen.pdf"),
        ("sha256", "q" * 64),
        ("stored_path", "originals/../secret.pdf"),
        ("stored_path", "private/evaluation.pdf"),
        ("http_status", 202),
        ("pdf_signature_checked", False),
        ("media_type", "text/html"),
        ("size_bytes", 1),
        ("size_bytes", -1),
        ("status", "unknown"),
    ],
)
def test_pinned_but_invalid_source_rejected(
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    fixture = packet_fixture(tmp_path)
    fixture.rows[0][field] = value
    with pytest.raises((ValueError, TypeError)):
        inspect_packet(fixture.root, fixture.pin())


@pytest.mark.parametrize(
    "url",
    [
        "http://example.org/alpha.pdf",
        "https://u:p@example.org/alpha.pdf",
        "https://example.org:8443/alpha.pdf",
        "https://example.org/alpha.pdf#fragment",
        "https://example.org/alpha .pdf",
    ],
)
def test_requested_url_must_remain_in_declared_https_scope(
    tmp_path: Path,
    url: str,
) -> None:
    fixture = packet_fixture(tmp_path)
    fixture.rows[0]["url"] = url
    records(fixture.request["sources"])[0]["url"] = url
    with pytest.raises(ValueError, match="HTTPS scope"):
        inspect_packet(fixture.root, fixture.pin())


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("directory", "private/test-packet"),
        ("source_revision", "main"),
        ("request_sha256", "bad"),
        ("allowed_hosts", []),
        ("allowed_hosts", ["example.org", "example.org"]),
        ("allowed_hosts", ["example.org/path"]),
        ("known_census_gaps", [""]),
    ],
)
def test_invalid_registry_spec(tmp_path: Path, field: str, value: object) -> None:
    fixture = packet_fixture(tmp_path)
    entry = fixture.spec.as_dict()
    entry[field] = value
    with pytest.raises((ValueError, TypeError)):
        PacketSpec.from_record(entry)


def test_changed_metadata_not_authorized_by_self_hash(tmp_path: Path) -> None:
    fixture = packet_fixture(tmp_path)
    (fixture.root / "request.json").write_text("{}")
    with pytest.raises(ValueError, match="pinned metadata changed"):
        inspect_packet(fixture.root, fixture.spec)


@pytest.mark.parametrize("kind", ["missing", "extra", "duplicate", "empty"])
def test_exact_source_membership(tmp_path: Path, kind: str) -> None:
    fixture = packet_fixture(tmp_path)
    rows = fixture.rows
    if kind == "missing":
        rows.pop()
    elif kind == "extra":
        rows.append({**rows[1], "source_id": "gamma"})
    elif kind == "duplicate":
        rows.append(dict(rows[0]))
    else:
        rows.clear()
    with pytest.raises(
        ValueError, match=r"membership|source count|duplicate|capture|reason"
    ):
        inspect_packet(fixture.root, fixture.pin())


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("sha256", "a" * 64),
        ("error", ""),
        ("status", "pretend_success"),
    ],
)
def test_failures_cannot_hide_objects_or_reasons(
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    fixture = packet_fixture(tmp_path)
    fixture.rows[1][field] = value
    with pytest.raises(
        ValueError, match=r"membership|source count|duplicate|capture|reason"
    ):
        inspect_packet(fixture.root, fixture.pin())


@pytest.mark.parametrize("content", [b"x" * len(PDF), b"%PDF-1.7\nno end marker"])
def test_pdf_transport_markers_are_checked(tmp_path: Path, content: bytes) -> None:
    fixture = packet_fixture(tmp_path)
    (fixture.root / "originals/alpha.pdf").write_bytes(content)
    fixture.rows[0].update(sha256=sha256_bytes(content), size_bytes=len(content))
    with pytest.raises(ValueError, match=r"marker|signature"):
        inspect_packet(fixture.root, fixture.pin())


def test_tamper_even_when_length_identical(tmp_path: Path) -> None:
    fixture = packet_fixture(tmp_path)
    (fixture.root / "originals/alpha.pdf").write_bytes(b"x" + PDF[1:])
    with pytest.raises(ValueError, match="hash mismatch"):
        inspect_packet(fixture.root, fixture.spec)


@pytest.mark.parametrize("kind", ["extra", "symlink", "fifo", "missing"])
def test_file_inventory_not_directory_discovery(tmp_path: Path, kind: str) -> None:
    fixture = packet_fixture(tmp_path)
    path = fixture.root / "originals/extra.pdf"
    if kind == "extra":
        path.write_bytes(PDF)
    elif kind == "symlink":
        path.symlink_to(fixture.root / "originals/alpha.pdf")
    elif kind == "fifo":
        os.mkfifo(path)
    else:
        (fixture.root / "originals/alpha.pdf").unlink()
    with pytest.raises(ValueError, match=r"inventory|symlink|regular"):
        inspect_packet(fixture.root, fixture.spec)


def test_total_budget_checked_before_reading_originals(tmp_path: Path) -> None:
    fixture = packet_fixture(tmp_path)
    fixture.rows[0]["size_bytes"] = MAX_PACKET_BYTES + 1
    (fixture.root / "originals/alpha.pdf").unlink()
    with pytest.raises(ValueError, match="before original reads"):
        inspect_packet(fixture.root, fixture.pin())


def test_fully_captured_packet_still_not_a_medallion_release(tmp_path: Path) -> None:
    fixture = packet_fixture(tmp_path)
    fixture.rows.pop()
    fixture.request["sources"] = records(fixture.request["sources"])[:1]
    fixture.manifest["source_count"] = 1
    fixture.spec = replace(fixture.spec, known_census_gaps=())
    result = inspect_packet(fixture.root, fixture.pin())
    assert result["acquisition_complete"]
    assert not result["gate_b_passed"]


def test_registry_rejects_empty_and_duplicate_packets(tmp_path: Path) -> None:
    fixture = packet_fixture(tmp_path)
    repository = fixture.registry()
    for packets in ([], [fixture.spec.as_dict(), fixture.spec.as_dict()]):
        atomic_json(
            repository / "data/sources/source-packets-v1.json",
            {
                "schema_version": 1,
                "packets": packets,
            },
        )
        with pytest.raises(ValueError, match=r"registry size|duplicate packet"):
            load_packet_registry(repository)


def test_regular_directory_required(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="regular directory"):
        inventory_paths(tmp_path / "absent")
