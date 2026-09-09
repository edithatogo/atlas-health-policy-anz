"""Synthetic, independently pinned original packets for offline contract tests."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

from australian_health_policy_atlas.hashing import sha256_bytes, sha256_file
from australian_health_policy_atlas.integrity import atomic_json
from australian_health_policy_atlas.packet_ingestion import PacketSpec

PDF = b"%PDF-1.7\nsynthetic transport fixture, not a real clinical policy\n%%EOF\n"


@dataclass
class PacketFixture:
    root: Path
    request: dict[str, object]
    manifest: dict[str, object]
    rows: list[dict[str, object]]
    spec: PacketSpec

    def pin(self) -> PacketSpec:
        atomic_json(self.root / "request.json", self.request)
        atomic_json(self.root / "capture-manifest.json", self.manifest)
        self.spec = replace(
            self.spec,
            request_sha256=sha256_file(self.root / "request.json"),
            capture_sha256=sha256_file(self.root / "capture-manifest.json"),
        )
        return self.spec

    def registry(self) -> Path:
        repository = self.root.parent.parent
        atomic_json(
            repository / "data/sources/source-packets-v1.json",
            {
                "schema_version": 1,
                "packets": [self.spec.as_dict()],
            },
        )
        return repository


def packet_fixture(tmp_path: Path) -> PacketFixture:
    identity = "test-packet"
    root = tmp_path / "source-packets" / identity
    original = root / "originals/alpha.pdf"
    original.parent.mkdir(parents=True)
    original.write_bytes(PDF)
    sources: list[dict[str, object]] = [
        {
            "source_id": name,
            "title": "Synthetic " + name,
            "url": "https://example.org/" + name + ".pdf",
            "licence": "CC0-1.0",
            "attribution": "Synthetic test",
            "rights_basis": "Authored fixture",
        }
        for name in ("alpha", "beta")
    ]
    rows: list[dict[str, object]] = [
        {
            **sources[0],
            "observed_at": "2026-09-10T00:00:00+00:00",
            "status": "captured_original",
            "sha256": sha256_bytes(PDF),
            "size_bytes": len(PDF),
            "stored_path": "originals/alpha.pdf",
            "http_status": 200,
            "final_url": sources[0]["url"],
            "parsing_qualified": False,
            "media_type": "application/pdf",
            "pdf_signature_checked": True,
        },
        {
            **sources[1],
            "observed_at": "2026-09-10T00:00:01+00:00",
            "status": "capture_failed",
            "sha256": None,
            "size_bytes": None,
            "stored_path": None,
            "parsing_qualified": False,
            "error": "HTTP 403",
        },
    ]
    result = PacketFixture(
        root,
        {"packet_id": identity, "sources": sources},
        {
            "schema_version": "source-packet-1.0",
            "packet_id": identity,
            "qualification": "source_staging_only_not_bronze_closure",
            "evaluation_included": False,
            "hugging_face_write": False,
            "source_count": 2,
            "captured_count": 1,
            "objects": rows,
        },
        rows,
        PacketSpec(
            identity,
            "source-packets/" + identity,
            "a" * 40,
            "b" * 64,
            "c" * 64,
            ("example.org",),
            ("Unlocated report",),
        ),
    )
    result.pin()
    return result
