"""Verify or publicly stage only registry-pinned original-document packets.

Missing credentials produce a blocked receipt, not a false publication pass.
Invalid data or remote verification failures remain nonzero process failures.
"""

from __future__ import annotations

import argparse
import os
import platform
from pathlib import Path

from australian_health_policy_atlas.hashing import sha256_file
from australian_health_policy_atlas.hub_staging import HfStore
from australian_health_policy_atlas.integrity import REVISION, atomic_json, sealed
from australian_health_policy_atlas.packet_ingestion import (
    inspect_packet,
    load_packet_registry,
    require_packet,
)
from australian_health_policy_atlas.packet_staging import (
    build_packet_stage,
    publish_packet_stage,
)

DATASET = "edithatogo/au-health-policy-atlas-bronze"


class Arguments(argparse.Namespace):
    """Closed-set operation, optional packet selection and explicit output locations."""

    mode: str = "verify"
    repository: Path = Path()
    workspace: Path = Path("build/source-packets")
    receipt: Path = Path("build/source-packets-receipt.json")
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


def execute(args: Arguments, *, token: str | None = None) -> dict[str, object]:
    """Perform offline verification before any optional authenticated publication.

    Returns:
        A sealed run receipt, with credential absence distinct from qualification.
        The token is neither serialized nor printed.

    """
    require_packet(args.mode in {"verify", "stage", "publish"}, "unsupported operation")
    identity = _execution_identity(args.repository)
    specs = load_packet_registry(args.repository)
    if args.packet_id is not None:
        specs = [spec for spec in specs if spec.packet_id == args.packet_id]
    require_packet(bool(specs), "packet is not registered")
    observations: list[dict[str, object]] = []
    publication: list[dict[str, object]] = []
    for spec in specs:
        source = args.repository / spec.directory
        observations.append(inspect_packet(source, spec))
        if args.mode != "verify":
            stage = args.workspace / spec.packet_id
            build_packet_stage(source, spec, stage)
            if args.mode == "publish" and token:
                publication.append(
                    publish_packet_stage(HfStore(DATASET, token), stage, spec)
                )
    blocked = args.mode == "publish" and not token
    return sealed({
        "schema_version": "1.0",
        "kind": "registered-source-packet-run",
        "operation": args.mode,
        "status": "blocked_missing_hf_token" if blocked else "verified",
        "observations": observations,
        "publication": publication,
        "dataset_id": DATASET,
        "execution": identity,
        "remote_bytes_verified": bool(publication),
        "network_used": bool(publication),
        "not_medallion_release": True,
        "gate_b_passed": False,
    })


def main() -> int:
    """Execute one bounded packet operation and retain its terminal-state receipt.

    Returns:
        Zero for completed verification or a reported missing-credential blocker.
        Execution exceptions propagate instead of being converted into success.

    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("verify", "stage", "publish"))
    parser.add_argument("--repository", type=Path, default=Path())
    parser.add_argument("--workspace", type=Path, default=Path("build/source-packets"))
    parser.add_argument(
        "--receipt", type=Path, default=Path("build/source-packets-receipt.json")
    )
    parser.add_argument("--packet-id")
    args = parser.parse_args(namespace=Arguments())
    atomic_json(
        args.receipt,
        {
            "status": "executing",
            "operation": args.mode,
            "not_medallion_release": True,
            "gate_b_passed": False,
        },
    )
    try:
        result = execute(
            args, token=os.environ.get("HF_TOKEN") if args.mode == "publish" else None
        )
    except (ValueError, TypeError, KeyError, OSError, RuntimeError) as error:
        atomic_json(
            args.receipt,
            sealed({
                "schema_version": "1.0",
                "kind": "registered-source-packet-failure",
                "status": "failed",
                "operation": args.mode,
                "error_type": type(error).__name__,
                "remote_bytes_verified": False,
                "publication_state": "not_verified",
                "not_medallion_release": True,
                "gate_b_passed": False,
            }),
        )
        print("Packet operation failed; see the sanitized failure receipt.")
        return 1
    atomic_json(args.receipt, result)
    print(result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
