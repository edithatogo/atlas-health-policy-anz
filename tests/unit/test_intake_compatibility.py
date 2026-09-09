"""Both preserved intake formats share exact-byte checks and independent replay."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import cast

import jsonschema
import pytest
from scripts import source_packets

from australian_health_policy_atlas.hashing import sha256_bytes
from australian_health_policy_atlas.integrity import read_json, sealed
from australian_health_policy_atlas.operations import load_collection, run_source
from australian_health_policy_atlas.packet_holdings import summarize_holdings
from australian_health_policy_atlas.packet_ingestion import (
    Layout,
    PacketSpec,
    inspect_packet,
    packet_metadata_paths,
)
from australian_health_policy_atlas.packet_staging import (
    build_packet_stage,
    publish_packet_stage,
    restore_packet_stage,
)
from australian_health_policy_atlas.records import record, records
from tests.intake_support import intake_fixture
from tests.packet_support import PDF, packet_fixture
from tests.unit.test_hub_staging_runtime import MemoryHub


def test_intake_preserves_raw_metadata_and_replays_without_originals(
    tmp_path: Path,
) -> None:
    fixture = intake_fixture(tmp_path)
    spec = fixture.spec
    result = inspect_packet(fixture.root, spec)
    assert result["source_count"] == 2
    assert result["captured_count"] == result["failed_count"] == 1
    failure = records(result["capture_failures"])[0]
    assert failure["observed_at"] == "2026-09-10T00:00:02+00:00"
    assert (
        failure["observed_at_basis"] == "batch_completion_not_individual_request_time"
    )
    assert records(result["objects"])[0]["observed_at"] == "2026-09-10T00:00:00+00:00"
    stage = tmp_path / "stage"
    manifest = build_packet_stage(fixture.root, spec, stage)
    assert (
        stage / "evidence/request.json"
    ).read_bytes() == fixture.request_path.read_bytes()
    assert (stage / "evidence/capture-manifest.json").read_bytes() == (
        fixture.root / "manifest.json"
    ).read_bytes()
    hub = MemoryHub()
    reference = publish_packet_stage(hub, stage, spec)
    (fixture.root / "originals/alpha.pdf").unlink()
    assert (
        restore_packet_stage(
            hub, spec, record(reference["reference"]), tmp_path / "restore"
        )
        == manifest
    )
    schema = read_json(Path("schemas/source-packet-staging-v1.json").read_bytes())
    jsonschema.validate(manifest, schema)
    assert not manifest["gate_b_passed"]


@pytest.mark.parametrize(
    ("target", "key", "value"),
    [
        ("request", "schema_version", True),
        ("manifest", "schema_version", True),
        ("request", "collection_id", "other"),
        ("manifest", "collection_id", "other"),
        ("request", "kind", "local-evaluation"),
        ("request", "medallion_promotion", True),
        ("manifest", "medallion_promotion", True),
        ("request", "evaluation_material_allowed", True),
        ("manifest", "evaluation_material", True),
        ("manifest", "code_revision", "main"),
        ("manifest", "captured_at", "2026-09-10T00:00:00"),
        ("manifest", "request_sha256", "e" * 64),
        ("request", "maximum_documents", 1),
        ("request", "maximum_documents", 257),
        ("request", "maximum_bytes_per_document", 0),
        ("request", "maximum_bytes_per_document", 33554433),
        ("request", "maximum_bytes_per_document", len(PDF) - 1),
        ("request", "maximum_total_bytes", 0),
        ("request", "maximum_total_bytes", 268435457),
        ("request", "maximum_total_bytes", len(PDF) - 1),
        ("manifest", "bytes", 0),
        ("manifest", "captured_count", 2),
        ("manifest", "requested_count", 1),
    ],
)
def test_intake_headers_and_counts_cannot_be_resealed_to_pass(
    tmp_path: Path, target: str, key: str, value: object
) -> None:
    fixture = intake_fixture(tmp_path)
    container = fixture.request if target == "request" else fixture.manifest
    container[key] = value
    fixture.pin(relink=key != "request_sha256")
    with pytest.raises((ValueError, TypeError)):
        inspect_packet(fixture.root, fixture.spec)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("status", "published"),
        ("remote_verification", True),
        ("original_unmodified", False),
        ("semantic_qualification", True),
        ("title", "Substituted title"),
        ("rights", "Substituted rights"),
        ("rights_evidence", "Substituted provenance"),
        ("attribution", "Substituted attribution"),
        ("id", "beta"),
    ],
)
def test_intake_provenance_mutation_is_rejected(
    tmp_path: Path, key: str, value: object
) -> None:
    fixture = intake_fixture(tmp_path)
    fixture.rows[0][key] = value
    fixture.pin()
    with pytest.raises(
        ValueError, match=r"intake|publication|original|provenance|source ID"
    ):
        inspect_packet(fixture.root, fixture.spec)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("requested_url", "https://other.example/alpha.pdf"),
        ("stored_path", "data/source-documents/other/originals/alpha.pdf"),
        ("stored_path", "data/source-documents/test-intake/originals/../alpha.pdf"),
        ("final_url", "http://example.org/alpha.pdf"),
        ("size_bytes", True),
        ("http_status", 403),
        ("media_type", "text/html"),
        ("observed_at", "2026-09-10T00:00:00"),
        ("sha256", "e" * 64),
    ],
)
def test_intake_receipt_mutation_is_rejected(
    tmp_path: Path, key: str, value: object
) -> None:
    fixture = intake_fixture(tmp_path)
    record(fixture.rows[0]["receipt"])[key] = value
    fixture.pin()
    with pytest.raises((ValueError, TypeError)):
        inspect_packet(fixture.root, fixture.spec)


def test_intake_failed_record_cannot_contain_a_captured_receipt(tmp_path: Path) -> None:
    fixture = intake_fixture(tmp_path)
    fixture.rows[1]["receipt"] = fixture.rows[0]["receipt"]
    fixture.pin()
    with pytest.raises(ValueError, match="failed intake"):
        inspect_packet(fixture.root, fixture.spec)


def test_legacy_identity_is_unchanged_and_cross_format_directory_is_rejected(
    tmp_path: Path,
) -> None:
    legacy = packet_fixture(tmp_path)
    assert "metadata_format" not in legacy.spec.as_dict()
    assert PacketSpec.from_record(legacy.spec.as_dict()) == legacy.spec
    for spec in (
        replace(legacy.spec, metadata_format="unknown"),
        replace(legacy.spec, metadata_format="finite-source-intake-1.0"),
        replace(legacy.spec, directory="data/source-documents/test-packet"),
    ):
        with pytest.raises(ValueError, match=r"metadata format|directory"):
            spec.validate()
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(
                {"schema_version": 1, "packets": [spec.as_dict()]},
                read_json(Path("schemas/source-packet-registry-v1.json").read_bytes()),
            )


def test_intake_split_metadata_layout_rejects_symlinks_and_wrong_root(
    tmp_path: Path,
) -> None:
    fixture = intake_fixture(tmp_path)
    with pytest.raises(ValueError, match="layout"):
        packet_metadata_paths(
            tmp_path / "not-the-source-root", fixture.spec, "original"
        )
    raw = fixture.request_path.read_bytes()
    outside = tmp_path / "elsewhere.json"
    outside.write_bytes(raw)
    fixture.request_path.unlink()
    fixture.request_path.symlink_to(outside)
    with pytest.raises(ValueError, match="symlink"):
        inspect_packet(fixture.root, fixture.spec)


def test_holdings_deduplicate_bytes_not_source_histories(tmp_path: Path) -> None:
    intake, legacy = intake_fixture(tmp_path), packet_fixture(tmp_path)
    a = inspect_packet(intake.root, intake.spec)
    b = inspect_packet(legacy.root, legacy.spec)
    holdings = summarize_holdings([a, b])
    assert summarize_holdings([b, a]) == holdings
    assert holdings["requested_source_record_count"] == 4
    assert holdings["captured_original_occurrences"] == 2
    assert holdings["failed_capture_record_count"] == 2
    assert holdings["unique_original_count"] == 1
    assert holdings["unique_original_bytes"] == len(PDF)
    assert holdings["repeated_original_occurrences"] == 1
    assert holdings["object_identities"] == [
        {"sha256": sha256_bytes(PDF), "size_bytes": len(PDF)}
    ]
    assert not holdings["policy_equivalence_inferred"]
    with pytest.raises(ValueError, match="duplicate holdings"):
        summarize_holdings([a, a])
    changed = sealed({**b, "integrity_verified": False})
    with pytest.raises(ValueError, match="unverified"):
        summarize_holdings([changed])
    records(b["objects"])[0]["size_bytes"] = len(PDF) + 1
    with pytest.raises(ValueError, match="duplicate object size"):
        summarize_holdings([a, sealed(b)])
    assert summarize_holdings([])["unique_original_count"] == 0


@pytest.mark.parametrize("budget", [0, -1, True, 1.5, "20", None])
def test_invalid_acquisition_budget_cannot_touch_hub(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, budget: object
) -> None:
    calls: list[str] = []
    hub = MemoryHub()
    monkeypatch.setattr(hub, "ensure_public", lambda: calls.append("called"))
    with pytest.raises(ValueError, match="positive integer"):
        run_source(
            load_collection()[0], tmp_path, hub=hub, request_budget=cast("int", budget)
        )
    assert not calls
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("layout", ["unknown", None])
def test_intake_shallow_path_and_unrecognised_layout_are_rejected(
    tmp_path: Path, layout: object
) -> None:
    fixture = intake_fixture(tmp_path)
    with pytest.raises(ValueError, match="layout"):
        packet_metadata_paths(Path("/x"), fixture.spec, "original")
    with pytest.raises(ValueError, match="layout"):
        packet_metadata_paths(fixture.root, fixture.spec, cast("Layout", layout))


@pytest.mark.parametrize("directory", ["data/source-intake", "data/source-documents"])
@pytest.mark.parametrize("output", ["receipt", "workspace", "summary"])
def test_cli_outputs_cannot_overwrite_either_preserved_intake_root(
    tmp_path: Path, directory: str, output: str
) -> None:
    args = source_packets.Arguments()
    args.repository = tmp_path
    setattr(args, output, tmp_path / directory / "preserved.json")
    with pytest.raises(source_packets.UnsafeOutputError, match="preserved"):
        source_packets.execute(args)
    assert not (tmp_path / directory).exists()


@pytest.mark.parametrize("field", ["source_count", "captured_count", "failed_count"])
def test_holdings_reject_contradictory_counts(tmp_path: Path, field: str) -> None:
    fixture = intake_fixture(tmp_path)
    observation = inspect_packet(fixture.root, fixture.spec)
    observation[field] = -1
    with pytest.raises(ValueError, match="counts disagree"):
        summarize_holdings([sealed(observation)])


@pytest.mark.parametrize(("field", "value"), [("sha256", "invalid"), ("size_bytes", 0)])
def test_holdings_reject_invalid_object_identity(
    tmp_path: Path, field: str, value: object
) -> None:
    fixture = intake_fixture(tmp_path)
    observation = inspect_packet(fixture.root, fixture.spec)
    records(observation["objects"])[0][field] = value
    with pytest.raises(ValueError, match="invalid holdings object"):
        summarize_holdings([sealed(observation)])
