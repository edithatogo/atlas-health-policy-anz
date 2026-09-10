"""Replay rejects altered or unsafe archives and preserves the existing Hub contract."""

from __future__ import annotations

import io
import stat
import zipfile
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from hypothesis import given
from hypothesis import strategies as st

from australian_health_policy_atlas import capture_bundle
from australian_health_policy_atlas.capture_bundle import export_bundle, restore_bundle
from australian_health_policy_atlas.hashing import sha256_bytes
from australian_health_policy_atlas.hub_staging import (
    publish_stage,
    restore_stage,
    verify_stage,
)
from australian_health_policy_atlas.integrity import sealed
from australian_health_policy_atlas.records import record
from tests.unit.test_crawl_runtime import policy
from tests.unit.test_hub_staging_runtime import MemoryHub, stage


def archive_entries(path: Path) -> list[tuple[zipfile.ZipInfo, bytes]]:
    with zipfile.ZipFile(path) as archive:
        return [(info, archive.read(info)) for info in archive.infolist()]


def rewrite(path: Path, entries: list[tuple[zipfile.ZipInfo, bytes]]) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        for info, data in entries:
            archive.writestr(info, data)


def repin(path: Path, reference: dict[str, object]) -> dict[str, object]:
    return sealed({
        **reference,
        "archive_sha256": sha256_bytes(path.read_bytes()),
        "archive_bytes": path.stat().st_size,
    })


def test_deterministic_bundle_replay_and_existing_hub_contract(tmp_path: Path) -> None:
    source = stage(tmp_path)
    a, b = tmp_path / "a.zip", tmp_path / "b.zip"
    reference = export_bundle(source, a, policy())
    assert reference == export_bundle(source, b, policy())
    assert a.read_bytes() == b.read_bytes()
    result = restore_bundle(a, reference, policy(), tmp_path / "replay")
    assert result == verify_stage(source)
    for info, _ in archive_entries(a):
        assert info.date_time == capture_bundle.FIXED_TIME
        assert info.compress_type == zipfile.ZIP_STORED
    hub = MemoryHub()
    publication = publish_stage(hub, tmp_path / "replay")
    assert (
        restore_stage(hub, record(publication["reference"]), tmp_path / "public-replay")
        == result
    )
    assert publication["remote_bytes_verified"] is True
    assert publication["gate_b_passed"] is False


@pytest.mark.parametrize(
    "field", ["manifest_sha256", "policy_sha256", "source_id", "kind", "gate_b_passed"]
)
def test_resealed_reference_cannot_override_evidence(
    tmp_path: Path, field: str
) -> None:
    path = tmp_path / "bundle.zip"
    reference = export_bundle(stage(tmp_path), path, policy())
    reference = sealed({**reference, field: "forged"})
    destination = tmp_path / "replay"
    with pytest.raises(ValueError, match="reference mismatch"):
        restore_bundle(path, reference, policy(), destination)
    assert not destination.exists()
    assert not list(tmp_path.glob(".atlas-replay-*"))


def test_independent_policy_is_required(tmp_path: Path) -> None:
    source = stage(tmp_path)
    path = tmp_path / "bundle.zip"
    reference = export_bundle(source, path, policy())
    wrong = replace(policy(), max_targets=1)
    with pytest.raises(ValueError, match="trusted policy"):
        restore_bundle(path, reference, wrong, tmp_path / "replay")
    with pytest.raises(ValueError, match="trusted policy"):
        export_bundle(source, tmp_path / "bad.zip", wrong)
    assert not (tmp_path / "bad.zip").exists()


@pytest.mark.parametrize(
    "name",
    [
        "../escape",
        "/absolute",
        "a/../escape",
        "./state.json",
        "a\\escape",
        "C:escape",
        "nul",
    ],
)
def test_unsafe_member_names_cannot_escape(tmp_path: Path, name: str) -> None:
    path = tmp_path / "bundle.zip"
    reference = export_bundle(stage(tmp_path), path, policy())
    entries = archive_entries(path)
    info = zipfile.ZipInfo(name)
    info.external_attr = (stat.S_IFREG | 0o644) << 16
    if name == "nul":
        path.write_bytes(path.read_bytes().replace(b"state.json", b"stat\x00.json"))
    else:
        entries.append((info, b"untrusted"))
        rewrite(path, entries)
    with pytest.raises((ValueError, zipfile.BadZipFile)):
        restore_bundle(path, repin(path, reference), policy(), tmp_path / "replay")
    assert not (tmp_path / "replay").exists()
    assert not (tmp_path / "escape").exists()


@pytest.mark.parametrize(
    "variant",
    ["symlink", "directory", "compressed", "extra", "missing", "tampered", "duplicate"],
)
def test_invalid_archive_inventory_after_repinning(
    tmp_path: Path, variant: str
) -> None:
    path = tmp_path / "bundle.zip"
    reference = export_bundle(stage(tmp_path), path, policy())
    entries = archive_entries(path)
    info, data = entries[0]
    if variant == "symlink":
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
    elif variant == "directory":
        info.external_attr = (stat.S_IFDIR | 0o755) << 16
    elif variant == "compressed":
        info.compress_type = zipfile.ZIP_DEFLATED
    elif variant == "extra":
        member = zipfile.ZipInfo("extra")
        member.external_attr = (stat.S_IFREG | 0o644) << 16
        entries.append((member, b"extra"))
    elif variant == "missing":
        entries = entries[:-1]
    elif variant == "tampered":
        entries[0] = (info, b"changed")
    else:
        entries.append((info, data))
    if variant == "duplicate":
        with pytest.warns(UserWarning, match="Duplicate name"):
            rewrite(path, entries)
    else:
        rewrite(path, entries)
    with pytest.raises((ValueError, zipfile.BadZipFile)):
        restore_bundle(path, repin(path, reference), policy(), tmp_path / "replay")
    assert not (tmp_path / "replay").exists()


def test_fixity_and_existing_paths(tmp_path: Path) -> None:
    source = stage(tmp_path)
    path = tmp_path / "bundle.zip"
    reference = export_bundle(source, path, policy())
    with pytest.raises(ValueError, match="exists"):
        export_bundle(source, path, policy())
    with pytest.raises(ValueError, match="overlaps"):
        export_bundle(source, source / "bad.zip", policy())
    with pytest.raises(ValueError, match="exists"):
        restore_bundle(path, reference, policy(), source)
    path.write_bytes(path.read_bytes()[:-1])
    with pytest.raises(ValueError, match="fixity"):
        restore_bundle(path, reference, policy(), tmp_path / "replay")


def test_byte_and_member_budgets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = stage(tmp_path)
    path = tmp_path / "bundle.zip"
    reference = export_bundle(source, path, policy())
    monkeypatch.setattr(capture_bundle, "MAX_BUNDLE_MEMBERS", 1)
    with pytest.raises(ValueError, match="member count"):
        restore_bundle(path, reference, policy(), tmp_path / "replay")
    with pytest.raises(ValueError, match="member budget"):
        export_bundle(source, tmp_path / "small.zip", policy())
    monkeypatch.setattr(capture_bundle, "MAX_BUNDLE_MEMBERS", 512)
    monkeypatch.setattr(capture_bundle, "MAX_BUNDLE_BYTES", 10)
    with pytest.raises(ValueError, match="budget"):
        restore_bundle(path, reference, policy(), tmp_path / "replay")
    with pytest.raises(ValueError, match="budget"):
        export_bundle(source, tmp_path / "small.zip", policy())


def test_symlink_archive_and_output_rejected(tmp_path: Path) -> None:
    path = tmp_path / "bundle.zip"
    reference = export_bundle(stage(tmp_path), path, policy())
    link = tmp_path / "symlink.zip"
    link.symlink_to(path)
    with pytest.raises(ValueError, match="unsafe archive"):
        restore_bundle(link, reference, policy(), tmp_path / "replay")
    dangling = tmp_path / "dangling"
    dangling.symlink_to(tmp_path / "not-present")
    with pytest.raises(ValueError, match="exists"):
        restore_bundle(path, reference, policy(), dangling)


def test_empty_zip_and_encrypted_flag_rejected(tmp_path: Path) -> None:
    path = tmp_path / "bundle.zip"
    reference = export_bundle(stage(tmp_path), path, policy())
    original = path.read_bytes()
    empty = io.BytesIO()
    with zipfile.ZipFile(empty, "w"):
        pass
    path.write_bytes(empty.getvalue())
    with pytest.raises(ValueError, match="member count"):
        restore_bundle(path, repin(path, reference), policy(), tmp_path / "replay")
    edited = bytearray(original)
    index = edited.index(b"PK\x01\x02")
    edited[index + 8] |= 1
    path.write_bytes(edited)
    with pytest.raises(ValueError, match="unencrypted"):
        restore_bundle(path, repin(path, reference), policy(), tmp_path / "replay")


@given(offset=st.integers(min_value=0, max_value=100_000))
def test_single_byte_mutation_fails_independent_pin(offset: int) -> None:
    with TemporaryDirectory() as directory:
        root = Path(directory)
        path = root / "capture.zip"
        reference = export_bundle(stage(root), path, policy())
        data = bytearray(path.read_bytes())
        data[offset % len(data)] ^= 1
        path.write_bytes(data)
        with pytest.raises(ValueError, match="fixity"):
            restore_bundle(path, reference, policy(), root / "replay")
        assert not (root / "replay").exists()
