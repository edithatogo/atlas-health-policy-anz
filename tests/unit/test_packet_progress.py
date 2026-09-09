"""Fault-isolation, interrupted publication and durable packet receipt contracts."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

import pytest
from scripts import source_packets

from australian_health_policy_atlas.integrity import (
    atomic_json,
    read_json,
    verify_seal,
)
from australian_health_policy_atlas.records import record, records
from tests.packet_support import PacketFixture, packet_fixture
from tests.support import ignoring_arguments
from tests.unit.test_hub_staging_runtime import MemoryHub

if TYPE_CHECKING:
    from pathlib import Path

    from australian_health_policy_atlas.hub_staging import HubStore
    from australian_health_policy_atlas.packet_ingestion import PacketSpec

SYNTHETIC = "synthetic-offline-fixture"


def packet_selection(tmp_path: Path) -> tuple[Path, list[PacketFixture]]:
    repository = tmp_path / "repository"
    fixtures: list[PacketFixture] = []
    for name in ("first", "second", "third"):
        fixture = packet_fixture(repository / name)
        target = repository / "source-packets" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        fixture.root.rename(target)
        fixture.root = target
        fixture.request["packet_id"] = name
        fixture.manifest["packet_id"] = name
        fixture.spec = replace(
            fixture.spec, packet_id=name, directory="source-packets/" + name
        )
        fixture.pin()
        fixtures.append(fixture)
    atomic_json(
        repository / "data/sources/source-packets-v1.json",
        {"schema_version": 1, "packets": [f.spec.as_dict() for f in fixtures]},
    )
    return repository, fixtures


def arguments(tmp_path: Path, repository: Path, mode: str) -> source_packets.Arguments:
    args = source_packets.Arguments()
    args.repository = repository
    args.workspace = tmp_path / "work"
    args.receipt = tmp_path / "receipt.json"
    args.mode = mode
    return args


def test_all_selected_packets_remain_after_middle_source_failure(
    tmp_path: Path,
) -> None:
    repository, fixtures = packet_selection(tmp_path)
    (fixtures[1].root / "originals/alpha.pdf").write_bytes(b"corrupt")
    snapshots: list[dict[str, object]] = []
    result = source_packets.execute(
        arguments(tmp_path, repository, "stage"), checkpoint=snapshots.append
    )
    assert result["status"] == "partial_failure"
    assert result["selected_packet_count"] == 3
    assert result["failed_packet_count"] == 1
    assert len(records(result["observations"])) == 2
    assert [item["phase"] for item in records(result["packets"])] == [
        "staged",
        "failed",
        "staged",
    ]
    assert records(result["packets"])[1]["failure_phase"] == "verifying"
    assert result["network_used"] is False
    assert result["network_attempted"] is False
    assert result["remote_effect_unknown"] is False
    assert [i["phase"] for i in records(snapshots[0]["packets"])] == ["queued"] * 3
    assert snapshots[0]["execution_complete"] is False
    assert result["execution_complete"] is True
    assert len({s["selection_sha256"] for s in snapshots}) == 1
    for index, snapshot in enumerate(snapshots, start=1):
        verify_seal(snapshot)
        assert snapshot["checkpoint_sequence"] == index
        assert snapshot["gate_b_passed"] is False


def test_success_survives_later_unknown_remote_effect_and_rerun(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, _fixtures = packet_selection(tmp_path)
    args = arguments(tmp_path, repository, "publish")
    hub = MemoryHub()
    snapshots: list[dict[str, object]] = []
    actual = source_packets.publish_packet_stage
    monkeypatch.setattr(source_packets, "HfStore", ignoring_arguments(lambda: hub))

    def interrupted_publication(
        store: HubStore, stage: Path, spec: PacketSpec
    ) -> dict[str, object]:
        progress = next(
            i
            for i in records(snapshots[-1]["packets"])
            if i["packet_id"] == spec.packet_id
        )
        assert progress["phase"] == "publishing"
        assert progress["network_attempted"] is True
        assert progress["remote_write_state"] == "unknown"
        result = actual(store, stage, spec)
        if spec.packet_id == "second":
            message = "synthetic confidential server message"
            raise RuntimeError(message)
        return result

    monkeypatch.setattr(source_packets, "publish_packet_stage", interrupted_publication)
    result = source_packets.execute(args, token=SYNTHETIC, checkpoint=snapshots.append)
    assert result["status"] == "partial_failure"
    assert result["published_packet_count"] == 2
    assert len(records(result["publication"])) == 2
    assert result["remote_bytes_verified"] is True
    assert result["all_selected_packets_published"] is False
    assert result["remote_effect_unknown"] is True
    assert result["network_used"] is True
    assert "confidential" not in str(result)
    assert records(result["packets"])[1]["failure_phase"] == "publishing"
    assert records(result["packets"])[1]["remote_write_state"] == "unknown"
    monkeypatch.setattr(source_packets, "publish_packet_stage", actual)
    rerun = source_packets.execute(args, token=SYNTHETIC)
    assert rerun["status"] == "verified"
    assert rerun["published_packet_count"] == 3
    assert rerun["all_selected_packets_published"] is True
    assert rerun["remote_effect_unknown"] is False
    assert all(
        i["reused_existing_package"] is True for i in records(rerun["publication"])
    )


@pytest.mark.parametrize("exception", [RuntimeError, ImportError, LookupError])
def test_remote_failure_never_claims_zero_network_use(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, exception: type[Exception]
) -> None:
    fixture = packet_fixture(tmp_path)
    args = arguments(tmp_path, fixture.registry(), "publish")

    def fail() -> object:
        message = "synthetic private exception content"
        raise exception(message)

    monkeypatch.setattr(source_packets, "HfStore", ignoring_arguments(fail))
    result = source_packets.execute(args, token=SYNTHETIC)
    assert result["status"] == "failed"
    assert result["network_attempted"] is True
    assert result["network_used"] is None
    assert result["remote_effect_unknown"] is True
    assert result["remote_bytes_verified"] is False
    assert "private" not in str(result)


@pytest.mark.parametrize("mode", ["stage", "publish"])
def test_valid_existing_stage_is_reverified_not_overwritten(
    tmp_path: Path, mode: str
) -> None:
    fixture = packet_fixture(tmp_path)
    args = arguments(tmp_path, fixture.registry(), mode)
    first = source_packets.execute(args)
    stage_manifest = args.workspace / fixture.spec.packet_id / "manifest.json"
    original = stage_manifest.read_bytes()
    assert source_packets.execute(args)["status"] == first["status"]
    assert stage_manifest.read_bytes() == original
    stage_manifest.write_bytes(b"corrupt")
    result = source_packets.execute(args)
    assert result["status"] == "failed"
    assert records(result["packets"])[0]["failure_phase"] == "staging"
    assert stage_manifest.read_bytes() == b"corrupt"
    assert result["network_attempted"] is False


def test_failed_checkpoint_stops_before_any_packet_action(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = packet_fixture(tmp_path)
    calls: list[str] = []

    def checkpoint(_result: dict[str, object]) -> None:
        message = "synthetic disk failure"
        raise OSError(message)

    def unexpected() -> dict[str, object]:
        calls.append("unexpected")
        return {}

    monkeypatch.setattr(
        source_packets, "inspect_packet", ignoring_arguments(unexpected)
    )
    with pytest.raises(OSError, match="disk failure"):
        source_packets.execute(
            arguments(tmp_path, fixture.registry(), "publish"),
            token=SYNTHETIC,
            checkpoint=checkpoint,
        )
    assert not calls


def test_process_interrupt_preserves_last_complete_checkpoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, _fixtures = packet_selection(tmp_path)
    snapshots: list[dict[str, object]] = []
    actual = source_packets.inspect_packet

    def interrupt(source: Path, spec: PacketSpec) -> dict[str, object]:
        if spec.packet_id == "second":
            raise KeyboardInterrupt
        return actual(source, spec)

    monkeypatch.setattr(source_packets, "inspect_packet", interrupt)
    with pytest.raises(KeyboardInterrupt):
        source_packets.execute(
            arguments(tmp_path, repository, "verify"), checkpoint=snapshots.append
        )
    last = snapshots[-1]
    verify_seal(last)
    assert last["execution_complete"] is False
    assert last["status"] == "executing"
    assert [i["phase"] for i in records(last["packets"])] == [
        "verified",
        "verifying",
        "queued",
    ]
    assert len(records(last["observations"])) == 1


def test_publication_interrupt_keeps_unknown_effect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = packet_fixture(tmp_path)
    snapshots: list[dict[str, object]] = []

    def interrupt() -> object:
        raise KeyboardInterrupt

    monkeypatch.setattr(source_packets, "HfStore", ignoring_arguments(interrupt))
    with pytest.raises(KeyboardInterrupt):
        source_packets.execute(
            arguments(tmp_path, fixture.registry(), "publish"),
            token=SYNTHETIC,
            checkpoint=snapshots.append,
        )
    assert snapshots[-1]["status"] == "executing"
    assert snapshots[-1]["remote_effect_unknown"] is True
    assert snapshots[-1]["network_used"] is None
    assert records(snapshots[-1]["packets"])[0]["phase"] == "publishing"


def test_only_safe_summary_labels_and_counts_are_rendered() -> None:
    result: dict[str, object] = {
        "status": "<script>untrusted</script>",
        "error_type": "confidential",
        "observations": ["private source"],
        "selected_packet_count": 3,
        "published_packet_count": 1,
        "failed_packet_count": 2,
        "remote_effect_unknown": True,
    }
    summary = source_packets.render_summary(result)
    assert "Unknown execution status" in summary
    assert "**3**" in summary
    assert "**yes**" in summary
    assert "Gate B remains false" in summary
    assert "script" not in summary
    assert "confidential" not in summary
    assert "private" not in summary


@pytest.mark.parametrize(
    "status",
    ["executing", "verified", "blocked_missing_hf_token", "partial_failure", "failed"],
)
def test_summary_handles_every_execution_status(status: str) -> None:
    result: dict[str, object] = {"status": status}
    assert "Unknown execution status" not in source_packets.render_summary(result)
    assert "Gate B remains false" in source_packets.render_summary(result)


@pytest.mark.parametrize("output", ["receipt", "summary", "workspace"])
def test_output_must_not_overlap_preserved_originals(
    tmp_path: Path, output: str
) -> None:
    fixture = packet_fixture(tmp_path)
    args = arguments(tmp_path, fixture.registry(), "verify")
    original = fixture.root / "originals/alpha.pdf"
    before = original.read_bytes()
    setattr(args, output, original)
    with pytest.raises(source_packets.UnsafeOutputError, match="preserved"):
        source_packets.execute(args)
    assert original.read_bytes() == before


def test_summary_receipt_collision_is_rejected(tmp_path: Path) -> None:
    fixture = packet_fixture(tmp_path)
    args = arguments(tmp_path, fixture.registry(), "verify")
    args.summary = args.receipt
    with pytest.raises(source_packets.UnsafeOutputError, match="different"):
        source_packets.execute(args)
    args.summary = args.workspace / "summary.md"
    with pytest.raises(source_packets.UnsafeOutputError, match="outside"):
        source_packets.execute(args)


def test_main_preserves_partial_result_and_returns_nonzero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, fixtures = packet_selection(tmp_path)
    (fixtures[1].root / "originals/alpha.pdf").write_bytes(b"corrupt")
    receipt, summary = tmp_path / "receipt.json", tmp_path / "summary.md"
    monkeypatch.setattr(
        "sys.argv",
        [
            "source_packets",
            "verify",
            "--repository",
            str(repository),
            "--receipt",
            str(receipt),
            "--summary",
            str(summary),
        ],
    )
    assert source_packets.main() == 1
    result = read_json(receipt.read_bytes())
    verify_seal(result)
    assert result["status"] == "partial_failure"
    assert len(records(result["observations"])) == 2
    assert "Partial failure" in summary.read_text()


def test_main_journal_failure_propagates_without_overwriting_progress(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = packet_fixture(tmp_path)
    receipt = tmp_path / "receipt.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "source_packets",
            "verify",
            "--repository",
            str(fixture.registry()),
            "--receipt",
            str(receipt),
        ],
    )
    calls = 0

    def persist(path: Path, value: dict[str, object]) -> None:
        nonlocal calls
        calls += 1
        if calls == 3:
            message = "synthetic filesystem failure"
            raise OSError(message)
        atomic_json(path, value)

    monkeypatch.setattr(source_packets, "atomic_json", persist)
    with pytest.raises(source_packets.CheckpointError, match="persistence failed"):
        source_packets.main()
    result = read_json(receipt.read_bytes())
    assert result["checkpoint_sequence"] == 2
    assert result["status"] == "executing"
    assert record(records(result["packets"])[0])["phase"] == "verifying"
