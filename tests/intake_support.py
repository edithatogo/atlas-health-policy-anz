"""Synthetic earlier-format intake fixtures, not real policies or live captures."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from australian_health_policy_atlas.hashing import sha256_bytes, sha256_file
from australian_health_policy_atlas.integrity import atomic_json
from australian_health_policy_atlas.packet_ingestion import PacketSpec
from tests.packet_support import PDF

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class IntakeFixture:
    root: Path
    request_path: Path
    request: dict[str, object]
    manifest: dict[str, object]
    rows: list[dict[str, object]]
    spec: PacketSpec

    def pin(self, *, relink: bool = True) -> PacketSpec:
        atomic_json(self.request_path, self.request)
        request_hash = sha256_file(self.request_path)
        if relink:
            self.manifest["request_sha256"] = request_hash
        atomic_json(self.root / "manifest.json", self.manifest)
        self.spec = replace(
            self.spec,
            request_sha256=request_hash,
            capture_sha256=sha256_file(self.root / "manifest.json"),
        )
        return self.spec


def intake_fixture(tmp_path: Path) -> IntakeFixture:
    identity = "test-intake"
    directory = "data/source-documents/" + identity
    root = tmp_path / directory
    original = root / "originals/alpha.pdf"
    original.parent.mkdir(parents=True)
    original.write_bytes(PDF)
    sources: list[dict[str, object]] = [
        {
            "id": name,
            "title": "Synthetic " + name,
            "url": "https://example.org/" + name + ".pdf",
            "rights": "Synthetic fixture rights",
            "rights_evidence": "Authored fixture",
            "attribution": "Synthetic test",
        }
        for name in ("alpha", "beta")
    ]
    rows: list[dict[str, object]] = [
        {
            **sources[0],
            "status": "captured_original_pdf",
            "original_unmodified": True,
            "semantic_qualification": False,
            "remote_verification": False,
            "receipt": {
                "requested_url": sources[0]["url"],
                "final_url": sources[0]["url"],
                "observed_at": "2026-09-10T00:00:00+00:00",
                "http_status": 200,
                "etag": None,
                "last_modified": None,
                "media_type": "application/pdf",
                "sha256": sha256_bytes(PDF),
                "size_bytes": len(PDF),
                "stored_path": directory + "/originals/alpha.pdf",
            },
        },
        {
            **sources[1],
            "status": "capture_failed",
            "remote_verification": False,
            "error": "Synthetic HTTP 403",
            "error_type": "HTTPError",
        },
    ]
    result = IntakeFixture(
        root,
        tmp_path / f"data/source-intake/{identity}/request.json",
        {
            "schema_version": 1,
            "collection_id": identity,
            "kind": "bounded-original-public-document-intake",
            "evaluation_material_allowed": False,
            "medallion_promotion": False,
            "maximum_documents": 2,
            "maximum_bytes_per_document": 33554432,
            "maximum_total_bytes": 209715200,
            "sources": sources,
        },
        {
            "schema_version": 1,
            "collection_id": identity,
            "evaluation_material": False,
            "medallion_promotion": False,
            "captured_at": "2026-09-10T00:00:02+00:00",
            "code_revision": "a" * 40,
            "request_sha256": "b" * 64,
            "requested_count": 2,
            "captured_count": 1,
            "bytes": len(PDF),
            "records": rows,
        },
        rows,
        PacketSpec(
            identity,
            directory,
            "a" * 40,
            "b" * 64,
            "c" * 64,
            ("example.org",),
            ("Synthetic full report is unlocated",),
            "finite-source-intake-1.0",
        ),
    )
    result.pin()
    return result
