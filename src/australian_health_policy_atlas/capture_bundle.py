"""Bounded transport of existing source stages, never a Bronze release.

Replay requires an independently trusted policy and archive reference. Only the
existing manifest, crawl state and referenced content-addressed bytes are bundled.
"""

from __future__ import annotations

import io
import stat
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

from .hashing import sha256_bytes, sha256_json
from .hub_staging import verify_stage
from .integrity import atomic_bytes, safe_path, sealed, verify_seal
from .packet_ingestion import require_packet
from .records import integer, records, string

if TYPE_CHECKING:
    from .crawl import CrawlPolicy

MAX_BUNDLE_BYTES = 2 * 1024 * 1024
MAX_BUNDLE_MEMBERS = 512
FIXED_TIME = (1980, 1, 1, 0, 0, 0)


def _bind(manifest: dict[str, object], policy: CrawlPolicy) -> None:
    policy.validate()
    require_packet(
        manifest["source_id"] == policy.source_id
        and manifest["policy_sha256"] == sha256_json(policy.as_dict()),
        "bundle does not match independently trusted policy",
    )


def _reference(data: bytes, manifest: dict[str, object]) -> dict[str, object]:
    return sealed({
        "schema_version": "1.0",
        "kind": "bounded-source-capture-bundle",
        "archive_sha256": sha256_bytes(data),
        "archive_bytes": len(data),
        "manifest_sha256": manifest["sha256"],
        "policy_sha256": manifest["policy_sha256"],
        "source_id": manifest["source_id"],
        "not_medallion_release": True,
        "gate_b_passed": False,
    })


def _archive(stage: Path, manifest: dict[str, object]) -> bytes:
    expected = {
        string(row["path"]): (string(row["sha256"]), integer(row["size_bytes"]))
        for row in records(manifest["files"])
    }
    header = (stage / "manifest.json").read_bytes()
    expected["manifest.json"] = sha256_bytes(header), len(header)
    require_packet(len(expected) <= MAX_BUNDLE_MEMBERS, "bundle member budget exceeded")
    require_packet(
        sum(size for _, size in expected.values()) <= MAX_BUNDLE_BYTES,
        "bundle byte budget exceeded",
    )
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, (digest, size) in sorted(expected.items()):
            path = safe_path(stage, name)
            require_packet(path.stat().st_size == size, "stage size changed")
            with path.open("rb") as stream:
                data = stream.read(size + 1)
            require_packet(
                len(data) == size and sha256_bytes(data) == digest,
                "stage bytes changed during transport",
            )
            member = zipfile.ZipInfo(name, FIXED_TIME)
            member.create_system = 3
            member.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(member, data)
    data = output.getvalue()
    require_packet(len(data) <= MAX_BUNDLE_BYTES, "bundle archive budget exceeded")
    return data


def export_bundle(
    stage: Path, destination: Path, policy: CrawlPolicy
) -> dict[str, object]:
    """Export a verified source stage into a bounded deterministic stored ZIP.

    Returns:
        A sealed archive reference, not a signature or publication receipt.
        Existing outputs and outputs within source stages are refused.

    """
    require_packet(
        not destination.exists() and not destination.is_symlink(),
        "bundle destination already exists",
    )
    require_packet(
        not destination.resolve().is_relative_to(stage.resolve()),
        "bundle output overlaps source stage",
    )
    manifest = verify_stage(stage)
    _bind(manifest, policy)
    data = _archive(stage, manifest)
    reference = _reference(data, manifest)
    with TemporaryDirectory(prefix="atlas-bundle-check-") as directory:
        _restore(data, reference, policy, Path(directory))
    atomic_bytes(destination, data)
    return reference


def _validate_members(archive: zipfile.ZipFile, root: Path) -> list[zipfile.ZipInfo]:
    members = archive.infolist()
    require_packet(
        0 < len(members) <= MAX_BUNDLE_MEMBERS, "invalid bundle member count"
    )
    names: set[str] = set()
    total = 0
    for member in members:
        name = member.filename
        safe_path(root, name)
        require_packet(
            name == member.orig_filename and name not in names,
            "duplicate or ambiguous archive member",
        )
        require_packet(
            member.compress_type == zipfile.ZIP_STORED
            and member.flag_bits & ~0x800 == 0
            and stat.S_ISREG(member.external_attr >> 16)
            and not member.is_dir(),
            "only unencrypted stored regular files are permitted",
        )
        require_packet(
            0 <= member.file_size == member.compress_size <= MAX_BUNDLE_BYTES,
            "invalid bundle member size",
        )
        total += member.file_size
        names.add(name)
    require_packet(total <= MAX_BUNDLE_BYTES, "bundle expansion budget exceeded")
    require_packet({"manifest.json", "state.json"} <= names, "missing stage metadata")
    return members


def _restore(
    data: bytes, reference: dict[str, object], policy: CrawlPolicy, root: Path
) -> dict[str, object]:
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        members = _validate_members(archive, root)
        for member in members:
            with archive.open(member) as stream:
                payload = stream.read(member.file_size + 1)
            require_packet(len(payload) == member.file_size, "archive length mismatch")
            atomic_bytes(safe_path(root, member.filename), payload)
    manifest = verify_stage(root)
    _bind(manifest, policy)
    require_packet(reference == _reference(data, manifest), "bundle reference mismatch")
    return manifest


def restore_bundle(
    archive: Path,
    reference: dict[str, object],
    policy: CrawlPolicy,
    destination: Path,
) -> dict[str, object]:
    """Verify stage evidence before installing a fresh replay directory.

    Returns:
        A verified ordinary source-stage manifest, usable by publish_stage.
        Invalid input never installs a partial destination. The caller supplies
        independent pins; single-owner paths, not hostile concurrent use, are assumed.

    """
    policy.validate()
    verify_seal(reference)
    require_packet(
        not destination.exists() and not destination.is_symlink(),
        "replay destination already exists",
    )
    require_packet(archive.is_file() and not archive.is_symlink(), "unsafe archive")
    require_packet(
        0 < archive.stat().st_size <= MAX_BUNDLE_BYTES, "archive byte budget exceeded"
    )
    with archive.open("rb") as stream:
        data = stream.read(MAX_BUNDLE_BYTES + 1)
    require_packet(
        len(data) == integer(reference["archive_bytes"])
        and len(data) <= MAX_BUNDLE_BYTES
        and sha256_bytes(data) == reference["archive_sha256"],
        "archive fixity mismatch",
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(
        prefix=".atlas-replay-", dir=destination.parent
    ) as directory:
        root = Path(directory) / "stage"
        root.mkdir()
        manifest = _restore(data, reference, policy, root)
        root.rename(destination)
    return manifest
