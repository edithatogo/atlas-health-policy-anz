"""Verify or publicly stage registry-pinned originals with per-packet checkpoints.

Missing credentials are explicit blockers. Packet faults retain earlier results
and do not suppress unrelated work. Journal failure stops further side effects.
"""

from __future__ import annotations

import argparse
import os
import platform
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from australian_health_policy_atlas.hashing import sha256_file
from australian_health_policy_atlas.hub_staging import HfStore
from australian_health_policy_atlas.integrity import (
    REVISION,
    atomic_bytes,
    atomic_json,
    sealed,
)
from australian_health_policy_atlas.packet_ingestion import (
    inspect_packet,
    load_packet_registry,
    require_packet,
)
from australian_health_policy_atlas.packet_progress import PacketProgress, PacketRun
from australian_health_policy_atlas.packet_staging import (
    build_packet_stage,
    publish_packet_stage,
    verify_packet_stage,
)
from australian_health_policy_atlas.records import integer, string

if TYPE_CHECKING:
    from collections.abc import Callable

DATASET = "edithatogo/au-health-policy-atlas-bronze"


class CheckpointError(Exception):
    """The durable journal could not be written; no further packet may run."""


class UnsafeOutputError(Exception):
    """An output location overlaps preserved inputs or a staging directory."""


class Arguments(argparse.Namespace):
    """Closed-set operation, optional packet selection and explicit output locations."""

    mode: str = "verify"
    repository: Path = Path()
    workspace: Path = Path("build/source-packets")
    receipt: Path = Path("build/source-packets-receipt.json")
    summary: Path | None = None
    packet_id: str | None = None


def _execution_identity(repository: Path) -> dict[str, object]:
    revision = os.environ.get("GITHUB_SHA")
    require_packet(
        revision is None or bool(REVISION.fullmatch(revision)),
        "invalid execution revision",
    )
    lock = repository / "uv.lock"
    return {
        "code_revision": revision,
        "workflow_run_id": os.environ.get("GITHUB_RUN_ID"),
        "python": platform.python_version(),
        "lock_sha256": sha256_file(lock) if lock.is_file() else None,
        "code_revision_observed": revision is not None,
    }


def _check_output_paths(args: Arguments) -> None:
    inputs = (
        args.repository / "source-packets",
        args.repository / "data/sources",
        args.repository / "uv.lock",
    )
    outputs = [args.receipt, args.workspace]
    if args.summary is not None:
        outputs.append(args.summary)
    for path in outputs:
        for source in inputs:
            if path.resolve().is_relative_to(source.resolve()):
                message = "output overlaps preserved packet inputs"
                raise UnsafeOutputError(message)
    reports = [args.receipt] + ([args.summary] if args.summary is not None else [])
    if any(path.resolve().is_relative_to(args.workspace.resolve()) for path in reports):
        message = "receipt and summary must be outside the staging workspace"
        raise UnsafeOutputError(message)
    if args.summary is not None and args.summary.resolve() == args.receipt.resolve():
        message = "summary and receipt must be different files"
        raise UnsafeOutputError(message)


def _attempt(
    item: PacketProgress, action: Callable[[], dict[str, object]]
) -> dict[str, object] | None:
    try:
        return action()
    except Exception as error:  # ruff: ignore[blind-except] - Bounded per-packet fault barrier; interruptions and checkpoint writes remain outside it.
        item.failure_phase = item.phase
        item.error_type = type(error).__name__
        item.phase = "failed"
        return None


def _stage(args: Arguments, item: PacketProgress) -> dict[str, object]:
    source = args.repository / item.spec.directory
    destination = args.workspace / item.spec.packet_id
    if destination.is_dir() and any(destination.iterdir()):
        return verify_packet_stage(destination, item.spec)
    return build_packet_stage(source, item.spec, destination)


def _publish(args: Arguments, item: PacketProgress, token: str) -> dict[str, object]:
    return publish_packet_stage(
        HfStore(DATASET, token), args.workspace / item.spec.packet_id, item.spec
    )


def _run_packet(
    args: Arguments,
    item: PacketProgress,
    token: str | None,
    emit: Callable[[], dict[str, object]],
) -> None:
    item.phase = "verifying"
    emit()
    item.observation = _attempt(
        item, partial(inspect_packet, args.repository / item.spec.directory, item.spec)
    )
    if item.observation is None:
        emit()
        return
    item.phase = "verified"
    emit()
    if args.mode == "verify":
        return
    item.phase = "staging"
    emit()
    manifest = _attempt(item, partial(_stage, args, item))
    if manifest is None:
        emit()
        return
    item.stage_sha256 = string(manifest["sha256"])
    item.phase = "staged"
    emit()
    if args.mode != "publish":
        return
    if not token:
        item.phase = "blocked_missing_hf_token"
        emit()
        return
    item.phase = "publishing"
    item.network_attempted = True
    emit()
    item.publication = _attempt(item, partial(_publish, args, item, token))
    if item.publication is not None:
        item.phase = "published"
    emit()


def execute(
    args: Arguments,
    *,
    token: str | None = None,
    checkpoint: Callable[[dict[str, object]], None] | None = None,
) -> dict[str, object]:
    """Run a finite packet selection with fault isolation and detached checkpoints.

    Returns:
        A sealed run receipt. Partial failure is not a success; earlier verified
        publications and every selected packet's disposition remain present.
        Checkpoint failures and process interruptions propagate immediately.

    """
    _check_output_paths(args)
    require_packet(args.mode in {"verify", "stage", "publish"}, "unsupported operation")
    identity = _execution_identity(args.repository)
    specs = load_packet_registry(args.repository)
    if args.packet_id is not None:
        specs = [spec for spec in specs if spec.packet_id == args.packet_id]
    require_packet(bool(specs), "packet is not registered")
    run = PacketRun(args.mode, DATASET, identity, [PacketProgress(s) for s in specs])

    def emit() -> dict[str, object]:
        result = run.snapshot()
        if checkpoint is not None:
            checkpoint(result)
        return result

    emit()
    for item in run.items:
        _run_packet(args, item, token, emit)
    run.complete = True
    return emit()


def render_summary(result: dict[str, object]) -> str:
    """Render fixed status labels and numeric counts, never source or error text.

    Returns:
        Safe Markdown for an Actions job summary or a local status report.

    """
    labels = {
        "executing": "Execution incomplete; inspect the latest packet checkpoint.",
        "verified": "Requested verification completed; publication is counted below.",
        "blocked_missing_hf_token": "Publication blocked: HF_TOKEN is unavailable.",
        "partial_failure": "Partial failure: retained successes do not clear failures.",
        "failed": "Execution failed; inspect the sanitized packet dispositions.",
    }
    status = labels.get(string(result["status"]), "Unknown execution status.")
    selected = integer(result.get("selected_packet_count", 0))
    failed = integer(result.get("failed_packet_count", 0))
    published = integer(result.get("published_packet_count", 0))
    unknown = result.get("remote_effect_unknown") is True
    return (
        "## Atlas source-packet execution\n\n"
        f"{status}\n\n"
        f"Selected packets: **{selected}**. Failed packets: **{failed}**. "
        f"Remotely verified packets: **{published}**.\n\n"
        f"Remote effect still unknown: **{'yes' if unknown else 'no'}**.\n\n"
        "A green blocked job is not an upload. Verified packets may already have "
        "existed remotely; these counts do not claim new writes.\n\n"
        "**Staging only. Bronze Gate B remains false.**\n"
    )


def _persist(args: Arguments, result: dict[str, object]) -> None:
    try:
        atomic_json(args.receipt, result)
        if args.summary is not None:
            atomic_bytes(args.summary, render_summary(result).encode())
    except OSError:
        message = "checkpoint persistence failed; stopping before further side effects"
        raise CheckpointError(message) from None


def main() -> int:
    """Run with durable checkpoints before and after every bounded packet phase.

    Returns:
        One for failed or partially failed execution; zero for verification or a
        reported credential blocker. Persistence failures and interrupts propagate.

    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("verify", "stage", "publish"))
    parser.add_argument("--repository", type=Path, default=Path())
    parser.add_argument("--workspace", type=Path, default=Path("build/source-packets"))
    parser.add_argument(
        "--receipt", type=Path, default=Path("build/source-packets-receipt.json")
    )
    parser.add_argument("--summary", type=Path)
    parser.add_argument("--packet-id")
    args = parser.parse_args(namespace=Arguments())
    _check_output_paths(args)
    try:
        result = execute(
            args,
            token=os.environ.get("HF_TOKEN") if args.mode == "publish" else None,
            checkpoint=partial(_persist, args),
        )
    except (ValueError, TypeError, KeyError, OSError, RuntimeError) as error:
        result = sealed({
            "schema_version": "1.1",
            "kind": "registered-source-packet-failure",
            "status": "failed",
            "operation": args.mode,
            "error_type": type(error).__name__,
            "remote_bytes_verified": False,
            "publication_state": "not_verified",
            "remote_effect_unknown": args.mode == "publish",
            "not_medallion_release": True,
            "gate_b_passed": False,
        })
    _persist(args, result)
    print(result["status"])
    return int(result["status"] in {"failed", "partial_failure"})


if __name__ == "__main__":
    raise SystemExit(main())
