"""Reconstructible packet staging using the existing public HubStore boundary.

Publication of verified originals is not Bronze closure, policy interpretation,
or native SourceRight/CiteWeft/Authentext qualification.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .hub_staging import HubStore

import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from .hashing import canonical_json_bytes, sha256_bytes, sha256_file
from .integrity import (
    REVISION,
    SHA256,
    atomic_bytes,
    atomic_json,
    read_json,
    safe_path,
    sealed,
    verify_seal,
)
from .packet_ingestion import (
    MAX_METADATA_BYTES,
    MAX_OBJECT_BYTES,
    MAX_PACKET_BYTES,
    MAX_SOURCES,
    PacketSpec,
    inspect_packet,
    inventory_paths,
    packet_metadata_paths,
    require_packet,
)
from .records import integer, record, records, string

METADATA = ("request.json", "capture-manifest.json")


def _rows(observation: dict[str, object]) -> bytes:
    return b"".join(
        canonical_json_bytes(row) + b"\n" for row in records(observation["objects"])
    )


def _candidate(
    observation: dict[str, object], files: list[dict[str, object]]
) -> dict[str, object]:
    return sealed({
        "schema_version": "1.0",
        "kind": "source-packet-staging-package",
        "origin": observation["origin"],
        "observation": observation,
        "files": files,
        "not_medallion_release": True,
        "gate_b_passed": False,
    })


def _empty_destination(root: Path, origin: Path | None = None) -> None:
    require_packet(not root.is_symlink(), "symlinked destination")
    safe_path(root.parent, root.name)
    require_packet(
        not root.exists() or (root.is_dir() and not any(root.iterdir())),
        "destination must be absent or empty",
    )
    if origin is not None:
        require_packet(
            not root.resolve().is_relative_to(origin.resolve())
            and not origin.resolve().is_relative_to(root.resolve()),
            "stage and original packet must not overlap",
        )


def build_packet_stage(
    source: Path, spec: PacketSpec, destination: Path
) -> dict[str, object]:
    """Copy only independently verified originals and pinned acquisition metadata.

    Returns:
        The deterministic staging manifest after clean local verification. No
        code, evaluation, prompts, traces or arbitrary adjacent files are copied.

    """
    _empty_destination(destination, source)
    observation = inspect_packet(source, spec)
    require_packet(observation["captured_count"] != 0, "no originals to stage")
    for name, original in zip(
        METADATA, packet_metadata_paths(source, spec, "original"), strict=True
    ):
        atomic_bytes(safe_path(destination, "evidence/" + name), original.read_bytes())
    for row in records(observation["objects"]):
        target = safe_path(destination, string(row["dataset_path"]))
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            shutil.copyfile(safe_path(source, string(row["original_path"])), target)
    atomic_bytes(destination / "records.jsonl", _rows(observation))
    files: list[dict[str, object]] = [
        {
            "path": name,
            "sha256": sha256_file(safe_path(destination, name)),
            "size_bytes": safe_path(destination, name).stat().st_size,
        }
        for name in sorted(inventory_paths(destination))
    ]
    manifest = _candidate(observation, files)
    atomic_json(destination / "manifest.json", manifest)
    return verify_packet_stage(destination, spec)


def verify_packet_stage(root: Path, spec: PacketSpec) -> dict[str, object]:
    """Recompute all identities from bytes and independent registry pins.

    Returns:
        The verified manifest. Neither its self-hash nor claimed inventory is
        sufficient without the independent original-packet verification.

    """
    manifest_path = safe_path(root, "manifest.json")
    require_packet(
        manifest_path.stat().st_size <= MAX_METADATA_BYTES, "oversized staging manifest"
    )
    manifest = read_json(manifest_path.read_bytes())
    verify_seal(manifest)
    observation = inspect_packet(root, spec, layout="staged")
    expected_paths = {"evidence/" + name for name in METADATA} | {"records.jsonl"}
    expected_paths |= {
        string(row["dataset_path"]) for row in records(observation["objects"])
    }
    require_packet(
        inventory_paths(root) == expected_paths | {"manifest.json"},
        "unexpected or missing stage member",
    )
    require_packet(
        (root / "records.jsonl").read_bytes() == _rows(observation),
        "derived rows disagree with captured evidence",
    )
    files: list[dict[str, object]] = [
        {
            "path": name,
            "sha256": sha256_file(safe_path(root, name)),
            "size_bytes": safe_path(root, name).stat().st_size,
        }
        for name in sorted(expected_paths)
    ]
    require_packet(
        manifest == _candidate(observation, files),
        "staging manifest disagrees with independent evidence",
    )
    return manifest


def _prefix(spec: PacketSpec, manifest: dict[str, object]) -> str:
    return f"staging/packets/{spec.packet_id}/{manifest['sha256']}"


def _remote_inventory(manifest: dict[str, object], spec: PacketSpec) -> None:
    verify_seal(manifest)
    require_packet(
        manifest.get("origin") == spec.as_dict()
        and manifest.get("kind") == "source-packet-staging-package"
        and manifest.get("not_medallion_release") is True
        and manifest.get("gate_b_passed") is False,
        "remote package origin or gate mismatch",
    )
    files = records(manifest["files"])
    require_packet(
        0 < len(files) <= MAX_SOURCES + 3, "remote inventory count exceeds budget"
    )
    names = [string(row["path"]) for row in files]
    require_packet(len(set(names)) == len(names), "duplicate remote inventory member")
    require_packet(
        {
            "evidence/request.json",
            "evidence/capture-manifest.json",
            "records.jsonl",
        }.issubset(names),
        "required remote metadata missing",
    )
    for item in files:
        name, size = string(item["path"]), integer(item["size_bytes"])
        metadata = name in {
            "evidence/request.json",
            "evidence/capture-manifest.json",
            "records.jsonl",
        }
        object_path = name.startswith("objects/") and name.endswith(".pdf")
        digest = name.removeprefix("objects/").removesuffix(".pdf")
        require_packet(
            metadata or (object_path and bool(SHA256.fullmatch(digest))),
            "undeclared remote file class",
        )
        require_packet(
            0 < size <= (MAX_METADATA_BYTES if metadata else MAX_OBJECT_BYTES),
            "remote object size exceeds budget",
        )
        require_packet(
            bool(SHA256.fullmatch(string(item["sha256"]))), "invalid remote object hash"
        )
    require_packet(
        sum(integer(row["size_bytes"]) for row in files)
        <= MAX_PACKET_BYTES + 3 * MAX_METADATA_BYTES,
        "remote packet size exceeds budget",
    )


def restore_packet_stage(
    hub: HubStore, spec: PacketSpec, reference: dict[str, object], destination: Path
) -> dict[str, object]:
    """Restore a pinned packet and re-verify it against independent source metadata.

    Returns:
        The reconstructed verified manifest, not a medallion release receipt.

    """
    spec.validate()
    _empty_destination(destination)
    verify_seal(reference)
    require_packet(
        reference.get("kind") == "verified-packet-reference"
        and reference.get("not_medallion_release") is True
        and reference.get("gate_b_passed") is False,
        "invalid packet reference contract",
    )
    require_packet(
        reference.get("origin") == spec.as_dict(), "reference origin mismatch"
    )
    revision = string(reference["revision"])
    require_packet(
        bool(REVISION.fullmatch(revision)), "immutable remote revision required"
    )
    expected_manifest = record(reference["manifest"])
    _remote_inventory(expected_manifest, spec)
    prefix = _prefix(spec, expected_manifest)
    raw = hub.get(prefix + "/manifest.json", revision)
    require_packet(
        raw == canonical_json_bytes(expected_manifest) + b"\n",
        "remote manifest bytes differ",
    )
    atomic_bytes(destination / "manifest.json", raw)
    for item in records(expected_manifest["files"]):
        relative = string(item["path"])
        path = safe_path(destination, relative)
        data = hub.get(prefix + "/" + relative, revision)
        require_packet(
            len(data) == item["size_bytes"] and sha256_bytes(data) == item["sha256"],
            "remote object bytes differ",
        )
        atomic_bytes(path, data)
    return verify_packet_stage(destination, spec)


def publish_packet_stage(
    hub: HubStore, stage: Path, spec: PacketSpec
) -> dict[str, object]:
    """Publish only verified members, then reconstruct them anonymously at one revision.

    Returns:
        A self-hashed observation containing the exact revision and manifest.
        HubStore contract tests can simulate this flow but are not live evidence.
        Identical packages are verified again without rewriting existing objects.

    """
    manifest = verify_packet_stage(stage, spec)
    hub.ensure_public()
    parent = hub.head()
    prefix = _prefix(spec, manifest)
    manifest_bytes = canonical_json_bytes(manifest) + b"\n"
    try:
        existing = hub.get(prefix + "/manifest.json", parent)
    except FileNotFoundError:
        existing = None
    if existing is None:
        files: dict[str, Path | bytes] = {
            prefix + "/" + string(row["path"]): safe_path(stage, string(row["path"]))
            for row in records(manifest["files"])
        }
        files[prefix + "/manifest.json"] = manifest_bytes
        revision = hub.put(files, parent=parent)
    else:
        require_packet(
            existing == manifest_bytes, "immutable package path already differs"
        )
        revision = parent
    reference = sealed({
        "schema_version": "1.0",
        "kind": "verified-packet-reference",
        "origin": spec.as_dict(),
        "revision": revision,
        "manifest": manifest,
        "not_medallion_release": True,
        "gate_b_passed": False,
    })
    with TemporaryDirectory(prefix="atlas-packet-replay-") as temporary:
        restored = restore_packet_stage(hub, spec, reference, Path(temporary))
    require_packet(restored == manifest, "clean reconstruction differs")
    return sealed({
        "schema_version": "1.0",
        "kind": "packet-publication-observation",
        "reference": reference,
        "remote_bytes_verified": True,
        "reused_existing_package": existing is not None,
        "not_medallion_release": True,
        "gate_b_passed": False,
    })
