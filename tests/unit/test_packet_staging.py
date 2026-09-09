"""Independent local and simulated-Hub reconstruction of bounded source packets."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

import pytest

from australian_health_policy_atlas.hashing import canonical_json_bytes
from australian_health_policy_atlas.integrity import (
    atomic_json,
    read_json,
    sealed,
    verify_seal,
)
from australian_health_policy_atlas.packet_ingestion import inspect_packet
from australian_health_policy_atlas.packet_staging import (
    build_packet_stage,
    publish_packet_stage,
    restore_packet_stage,
    verify_packet_stage,
)
from australian_health_policy_atlas.records import record, records, string
from tests.packet_support import PDF, packet_fixture
from tests.unit.test_hub_staging_runtime import MemoryHub

if TYPE_CHECKING:
    from pathlib import Path


def test_deterministic_local_stage_and_clean_reconstruction(tmp_path: Path) -> None:
    fixture = packet_fixture(tmp_path)
    # Arbitrary adjacent documents are never selected for publication.
    (fixture.root / "sensitive-evaluation.txt").write_text("do not publish")
    first, second = tmp_path / "first", tmp_path / "second"
    one = build_packet_stage(fixture.root, fixture.spec, first)
    two = build_packet_stage(fixture.root, fixture.spec, second)
    assert one == two
    assert (first / "manifest.json").read_bytes() == (
        second / "manifest.json"
    ).read_bytes()
    assert not (first / "sensitive-evaluation.txt").exists()
    assert len(records(one["files"])) == 4
    assert (fixture.root / "originals/alpha.pdf").read_bytes() == PDF
    assert not one["gate_b_passed"]
    hub = MemoryHub()
    publication = publish_packet_stage(hub, first, fixture.spec)
    verify_seal(publication)
    reference = record(publication["reference"])
    assert publication["remote_bytes_verified"]
    assert not publication["reused_existing_package"]
    assert (
        restore_packet_stage(hub, fixture.spec, reference, tmp_path / "restored") == one
    )
    revision = hub.head()
    repeated = publish_packet_stage(hub, first, fixture.spec)
    assert repeated["reused_existing_package"]
    assert hub.head() == revision
    assert not repeated["gate_b_passed"]
    assert len({ref for _, ref in hub.calls}) == 2


def test_deduplicate_bytes_not_source_membership(tmp_path: Path) -> None:
    fixture = packet_fixture(tmp_path)
    fixture.rows[1] = {
        **fixture.rows[0],
        **records(fixture.request["sources"])[1],
        "stored_path": "originals/beta.pdf",
    }
    (fixture.root / "originals/beta.pdf").write_bytes(PDF)
    fixture.manifest["captured_count"] = 2
    manifest = build_packet_stage(fixture.root, fixture.pin(), tmp_path / "stage")
    observation = record(manifest["observation"])
    assert observation["captured_count"] == 2
    assert observation["unique_object_count"] == 1
    assert len(records(manifest["files"])) == 4
    assert not observation["acquisition_complete"]  # Separate census gap remains.


@pytest.mark.parametrize(
    "kind", ["extra", "records", "metadata", "forged-gate", "forged-gap"]
)
def test_self_sealing_cannot_override_independent_evidence(
    tmp_path: Path, kind: str
) -> None:
    fixture = packet_fixture(tmp_path)
    stage = tmp_path / "stage"
    manifest = build_packet_stage(fixture.root, fixture.spec, stage)
    if kind == "extra":
        (stage / "extra.txt").write_text("untracked")
    elif kind == "records":
        (stage / "records.jsonl").write_text("{}\n")
    elif kind == "metadata":
        (stage / "evidence/request.json").write_text("{}")
    else:
        if kind == "forged-gate":
            manifest["gate_b_passed"] = True
        else:
            record(manifest["observation"])["capture_failures"] = []
        atomic_json(stage / "manifest.json", sealed(manifest))
    with pytest.raises(ValueError, match=r"stage|records|pinned|evidence"):
        verify_packet_stage(stage, fixture.spec)


def test_no_overwrite_and_no_overlap(tmp_path: Path) -> None:
    fixture = packet_fixture(tmp_path)
    build_packet_stage(fixture.root, fixture.spec, tmp_path / "stage")
    with pytest.raises(ValueError, match="empty"):
        build_packet_stage(fixture.root, fixture.spec, tmp_path / "stage")
    with pytest.raises(ValueError, match="overlap"):
        build_packet_stage(fixture.root, fixture.spec, fixture.root / "stage")
    target = tmp_path / "symlink"
    target.symlink_to(tmp_path / "absent", target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        build_packet_stage(fixture.root, fixture.spec, target)


def test_all_failed_verifies_but_cannot_publish_empty_dataset(tmp_path: Path) -> None:
    fixture = packet_fixture(tmp_path)
    fixture.rows[0] = {
        **fixture.rows[0],
        "status": "capture_failed",
        "sha256": None,
        "stored_path": None,
        "size_bytes": None,
        "error": "HTTP 403",
    }
    fixture.manifest["captured_count"] = 0
    (fixture.root / "originals/alpha.pdf").unlink()
    (fixture.root / "originals").rmdir()
    assert inspect_packet(fixture.root, fixture.pin())["captured_count"] == 0
    with pytest.raises(ValueError, match="no originals"):
        build_packet_stage(fixture.root, fixture.spec, tmp_path / "stage")


def test_private_destination_never_gets_bytes(tmp_path: Path) -> None:
    fixture = packet_fixture(tmp_path)
    stage = tmp_path / "stage"
    build_packet_stage(fixture.root, fixture.spec, stage)
    hub = MemoryHub()
    hub.public = False
    with pytest.raises(ValueError, match="private"):
        publish_packet_stage(hub, stage, fixture.spec)
    assert hub.calls == []
    assert len(hub.snapshots) == 1


@pytest.mark.parametrize("kind", ["object", "manifest", "missing"])
def test_remote_originals_reverified_not_upload_receipt_trusted(
    tmp_path: Path,
    kind: str,
) -> None:
    fixture = packet_fixture(tmp_path)
    stage = tmp_path / "stage"
    manifest = build_packet_stage(fixture.root, fixture.spec, stage)
    hub = MemoryHub()
    result = publish_packet_stage(hub, stage, fixture.spec)
    reference = record(result["reference"])
    snapshot = hub.snapshots[hub.head()]
    prefix = f"staging/packets/{fixture.spec.packet_id}/{manifest['sha256']}"
    key = (
        prefix + "/manifest.json"
        if kind == "manifest"
        else next(name for name in snapshot if "/objects/" in name)
    )
    if kind == "missing":
        del snapshot[key]
    else:
        snapshot[key] = b"corrupted"
    with pytest.raises((ValueError, FileNotFoundError)):
        restore_packet_stage(hub, fixture.spec, reference, tmp_path / "restored")
    with pytest.raises((ValueError, FileNotFoundError)):
        publish_packet_stage(hub, stage, fixture.spec)
    assert len(hub.snapshots) == 2  # No unverified pointer/overwrite.


@pytest.mark.parametrize(
    "kind",
    ["mutable", "origin", "gate", "duplicate", "traversal", "budget", "metadata"],
)
def test_bad_remote_references_rejected_before_requests(
    tmp_path: Path, kind: str
) -> None:
    fixture = packet_fixture(tmp_path)
    stage = tmp_path / "stage"
    build_packet_stage(fixture.root, fixture.spec, stage)
    hub = MemoryHub()
    reference = record(publish_packet_stage(hub, stage, fixture.spec)["reference"])
    manifest = record(reference["manifest"])
    if kind == "mutable":
        reference["revision"] = "main"
    elif kind == "origin":
        reference["origin"] = replace(fixture.spec, source_revision="b" * 40).as_dict()
    elif kind == "gate":
        reference["gate_b_passed"] = True
    else:
        rows = records(manifest["files"])
        if kind == "duplicate":
            rows.append(dict(rows[0]))
        elif kind == "traversal":
            rows[0]["path"] = "../escape"
        elif kind == "budget":
            rows[0]["size_bytes"] = 2**40
        else:
            rows.pop(0)
        manifest["files"] = rows
        reference["manifest"] = sealed(manifest)
    hub.calls.clear()
    with pytest.raises(
        ValueError,
        match=r"revision|origin|contract|inventory|file class|budget|metadata",
    ):
        restore_packet_stage(
            hub, fixture.spec, sealed(reference), tmp_path / "restored"
        )
    assert hub.calls == []


def test_forged_remote_manifest_resealed_is_still_not_truth(tmp_path: Path) -> None:
    fixture = packet_fixture(tmp_path)
    stage = tmp_path / "stage"
    build_packet_stage(fixture.root, fixture.spec, stage)
    hub = MemoryHub()
    reference = record(publish_packet_stage(hub, stage, fixture.spec)["reference"])
    original = record(reference["manifest"])
    old_prefix = f"staging/packets/{fixture.spec.packet_id}/{original['sha256']}"
    record(original["observation"])["acquisition_complete"] = True
    manifest = sealed(original)
    new_prefix = f"staging/packets/{fixture.spec.packet_id}/{manifest['sha256']}"
    moved: dict[str, Path | bytes] = {
        name.replace(old_prefix, new_prefix): raw
        for name, raw in hub.snapshots[hub.head()].items()
    }
    moved[new_prefix + "/manifest.json"] = canonical_json_bytes(manifest) + b"\n"
    reference.update(manifest=manifest, revision=hub.put(moved))
    with pytest.raises(ValueError, match="independent evidence"):
        restore_packet_stage(
            hub, fixture.spec, sealed(reference), tmp_path / "restored"
        )


def test_stage_receipt_is_not_dependent_on_local_absolute_path(tmp_path: Path) -> None:
    fixture = packet_fixture(tmp_path)
    stage = tmp_path / "stage"
    result = build_packet_stage(fixture.root, fixture.spec, stage)
    assert str(tmp_path) not in string((stage / "manifest.json").read_text())
    assert read_json((stage / "manifest.json").read_bytes()) == result
