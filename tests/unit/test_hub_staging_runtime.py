from __future__ import annotations

import pathlib
from pathlib import Path

import pytest

from australian_health_policy_atlas.crawl import run_crawl
from australian_health_policy_atlas.hub_staging import (
    build_stage,
    index_path,
    publish_stage,
    qualify_remote_bronze,
    restore_source,
    verify_stage,
)
from australian_health_policy_atlas.integrity import (
    atomic_json,
    canonical_json_bytes,
    read_json,
    sealed,
)
from tests.unit.test_crawl_runtime import fetcher, policy


class MemoryHub:
    """Simulated transactions only; never a live publication receipt."""

    def __init__(self) -> None:
        self.snapshots = {"0" * 40: {}}
        self.latest = "0" * 40
        self.public = True
        self.corrupt = False
        self.calls = []

    def ensure_public(self) -> None:
        if not self.public:
            raise ValueError("private target")

    def head(self):
        return self.latest

    def get(self, path, revision):
        self.calls.append((path, revision))
        if path not in self.snapshots[revision]:
            raise FileNotFoundError(path)
        value = self.snapshots[revision][path]
        return b"tampered" if self.corrupt and "/cas/" in path else value

    def put(self, files, *, parent=None):
        if parent is not None and parent != self.latest:
            raise ValueError("transaction conflict")
        result = dict(self.snapshots[self.latest])
        result.update({
            name: value.read_bytes() if isinstance(value, Path) else value
            for name, value in files.items()
        })
        revision = f"{len(self.snapshots):040x}"
        self.snapshots[revision] = result
        self.latest = revision
        return revision


def stage(tmp_path: pathlib.Path):
    root, destination = tmp_path / "crawl", tmp_path / "stage"
    run_crawl(
        policy(), root, fetch=fetcher({policy().seed_url: b"original exact bytes"})
    )
    build_stage(root, destination)
    return destination


def test_publish_restore_and_assess(tmp_path: pathlib.Path) -> None:
    source = stage(tmp_path)
    hub = MemoryHub()
    observation = publish_stage(hub, source)
    assert observation["remote_bytes_verified"]
    assert not observation["gate_b_passed"]
    assert len({revision for _, revision in hub.calls}) >= 2
    restored = tmp_path / "restore"
    result = restore_source(hub, policy(), restored, revision=hub.head())
    assert result["readiness"]["scope_complete"]
    assert not (restored / "manifest.json").exists()
    # Restored checkpoints can actually be resumed with no acquisition.
    run_crawl(
        policy(),
        restored,
        fetch=lambda *_args, **_kw: (_ for _ in ()).throw(AssertionError("recaptured")),
    )
    assessed = qualify_remote_bronze(
        hub, [policy()], census_sha256="a" * 64, code_revision="b" * 40
    )
    assert assessed["data_candidate_ready"]
    assert not assessed["gate_b_passed"]


def test_remote_corruption_never_publishes_index(tmp_path: pathlib.Path) -> None:
    source = stage(tmp_path)
    hub = MemoryHub()
    hub.corrupt = True
    with pytest.raises(ValueError, match="byte verification"):
        publish_stage(hub, source)
    assert index_path(policy()) not in hub.snapshots[hub.head()]


def test_private_hub_rejected_before_upload(tmp_path: pathlib.Path) -> None:
    hub = MemoryHub()
    hub.public = False
    with pytest.raises(ValueError, match="private"):
        publish_stage(hub, stage(tmp_path))
    assert len(hub.snapshots) == 1


def test_missing_source_blocks_remote_assessment() -> None:
    hub = MemoryHub()
    result = qualify_remote_bronze(
        hub, [policy()], census_sha256="a" * 64, code_revision="b" * 40
    )
    assert not result["data_candidate_ready"]
    assert len(result["blocked"]) == 1


@pytest.mark.parametrize("policies", [[], [policy(), policy()]])
def test_empty_or_duplicate_scope_refused(policies) -> None:
    with pytest.raises(ValueError, match="unique"):
        qualify_remote_bronze(
            MemoryHub(), policies, census_sha256="a" * 64, code_revision="b" * 40
        )


def test_bad_revision_refused() -> None:
    with pytest.raises(ValueError, match="identities"):
        qualify_remote_bronze(
            MemoryHub(), [policy()], census_sha256="a" * 64, code_revision="main"
        )


def test_local_extra_or_changed_file_rejected(tmp_path: pathlib.Path) -> None:
    source = stage(tmp_path)
    (source / "unexpected.txt").write_text("x")
    with pytest.raises(ValueError, match="untracked"):
        verify_stage(source)
    (source / "unexpected.txt").unlink()
    (source / "state.json").write_text("{}")
    with pytest.raises(ValueError, match="hash or length"):
        verify_stage(source)


def test_self_sealed_readiness_forgery_rejected(tmp_path: pathlib.Path) -> None:
    source = stage(tmp_path)
    manifest = read_json((source / "manifest.json").read_bytes())
    manifest["readiness"]["gate_b_passed"] = True
    atomic_json(source / "manifest.json", sealed(manifest))
    with pytest.raises(ValueError, match="disagrees"):
        verify_stage(source)


def test_stale_checkpoint_cannot_overwrite(tmp_path: pathlib.Path) -> None:
    source = stage(tmp_path)
    hub = MemoryHub()
    publish_stage(hub, source)
    previous = read_json(hub.get(index_path(policy()), hub.head()))
    previous["generation"] += 10
    hub.put({index_path(policy()): canonical_json_bytes(sealed(previous))})
    with pytest.raises(ValueError, match="rollback"):
        publish_stage(hub, source)


def test_incomplete_crawl_cannot_pass(tmp_path: pathlib.Path) -> None:
    root, source = tmp_path / "crawl", tmp_path / "stage"
    pages = {policy().seed_url: b'<a href="/a.pdf">Policy</a>'}
    run_crawl(policy(), root, request_budget=1, fetch=fetcher(pages))
    build_stage(root, source)
    hub = MemoryHub()
    publish_stage(hub, source)
    result = qualify_remote_bronze(
        hub, [policy()], census_sha256="a" * 64, code_revision="b" * 40
    )
    assert not result["data_candidate_ready"]


def test_nonempty_staging_destination_rejected(tmp_path: pathlib.Path) -> None:
    source = stage(tmp_path)
    with pytest.raises(ValueError, match="empty"):
        build_stage(tmp_path / "crawl", source)
