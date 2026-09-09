"""Run-mode and credential boundaries for the registry-only entry point."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from scripts import source_packets

from australian_health_policy_atlas.integrity import read_json
from australian_health_policy_atlas.records import record, records
from tests.packet_support import packet_fixture
from tests.support import ignoring_arguments
from tests.unit.test_hub_staging_runtime import MemoryHub

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize("mode", ["verify", "stage", "publish"])
def test_no_credentials_never_imply_publication(tmp_path: Path, mode: str) -> None:
    fixture = packet_fixture(tmp_path)
    args = source_packets.Arguments()
    args.repository, args.workspace = fixture.registry(), tmp_path / "work"
    args.mode = mode
    result = source_packets.execute(args)
    assert not result["network_used"]
    assert not result["remote_bytes_verified"]
    assert not result["gate_b_passed"]
    assert result["status"] == (
        "blocked_missing_hf_token" if mode == "publish" else "verified"
    )
    assert len(records(result["observations"])) == 1


def test_only_registered_packets_selected(tmp_path: Path) -> None:
    fixture = packet_fixture(tmp_path)
    args = source_packets.Arguments()
    args.repository = fixture.registry()
    args.packet_id = "unknown"
    with pytest.raises(ValueError, match="not registered"):
        source_packets.execute(args)
    args.packet_id = fixture.spec.packet_id
    assert len(records(source_packets.execute(args)["observations"])) == 1
    args.mode = "sensitive"
    with pytest.raises(ValueError, match="unsupported"):
        source_packets.execute(args)


def test_publication_simulated_not_live_hf(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = packet_fixture(tmp_path)
    args = source_packets.Arguments()
    args.repository, args.workspace = fixture.registry(), tmp_path / "work"
    args.mode = "publish"
    hub = MemoryHub()
    monkeypatch.setattr(source_packets, "HfStore", ignoring_arguments(lambda: hub))
    synthetic = "synthetic-token-not-real"
    result = source_packets.execute(args, token=synthetic)
    assert result["remote_bytes_verified"]
    assert result["status"] == "verified"
    assert "synthetic-token" not in str(result)
    assert not record(records(result["publication"])[0]["reference"])["gate_b_passed"]


def test_main_writes_offline_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = packet_fixture(tmp_path)
    output = tmp_path / "receipt.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "source_packets",
            "verify",
            "--repository",
            str(fixture.registry()),
            "--receipt",
            str(output),
        ],
    )
    assert source_packets.main() == 0
    assert read_json(output.read_bytes())["status"] == "verified"


def test_main_failure_receipt_does_not_leak_external_exception_text(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = packet_fixture(tmp_path)
    output = tmp_path / "receipt.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "source_packets",
            "publish",
            "--repository",
            str(fixture.registry()),
            "--receipt",
            str(output),
        ],
    )

    def error() -> object:
        message = "untrusted error with confidential token"
        raise RuntimeError(message)

    monkeypatch.setattr(source_packets, "execute", ignoring_arguments(error))
    assert source_packets.main() == 1
    result = read_json(output.read_bytes())
    assert result["status"] == "failed"
    assert result["publication_state"] == "not_verified"
    assert "confidential" not in str(result)


def test_execution_identity_not_guessed_and_invalid_revision_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = packet_fixture(tmp_path)
    args = source_packets.Arguments()
    args.repository = fixture.registry()
    (args.repository / "uv.lock").write_text("synthetic lock fixture")
    monkeypatch.setenv("GITHUB_SHA", "d" * 40)
    execution = record(source_packets.execute(args)["execution"])
    assert execution["code_revision"] == "d" * 40
    assert execution["code_revision_observed"]
    assert execution["lock_sha256"] is not None
    monkeypatch.setenv("GITHUB_SHA", "main")
    with pytest.raises(ValueError, match="execution revision"):
        source_packets.execute(args)
