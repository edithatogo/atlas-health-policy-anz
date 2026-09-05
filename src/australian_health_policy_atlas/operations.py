"""Bounded source orchestration, shared by Actions and CLI."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from .authorities import COLLECTIONS, authority_policies, source_bytes
from .capture import CapturePort, capture_url
from .crawl import CrawlPolicy, run_crawl
from .hub_staging import HfStore, HubStore, build_stage, publish_stage, restore_source
from .integrity import read_json
from .records import records, string

MAX_ACTIONS_MATRIX = 256


def load_policies(path: Path) -> list[CrawlPolicy]:
    """Read and validate unique source policies from the governed acquisition contract.

    Returns:
        Validated policies with unique source identities.

    Raises:
        ValueError: The supplied data violates the function's documented validation
        contract.

    """
    data = read_json(path.read_bytes())
    policies = [CrawlPolicy.from_record(row) for row in records(data["policies"])]
    if not policies or len({p.source_id for p in policies}) != len(policies):
        message = "source policies must be nonempty and unique"
        raise ValueError(message)
    return policies


def load_collection(
    name: str = "au-v1", directory: Path | None = None
) -> list[CrawlPolicy]:
    """Keep the AU v1 source universe frozen while selecting expanded ANZ sources.

    Returns:
        The result described above, retaining the declared return-type contract.

    Raises:
        ValueError: The supplied data violates the function's documented validation
        contract.

    """
    if name not in COLLECTIONS:
        message = "unknown acquisition collection"
        raise ValueError(message)
    if name in {"nz-v1", "authorities-v1"}:
        return authority_policies(name, directory)
    rows = read_json(source_bytes("crawl-policies-v1.json", directory))["policies"]
    policies = [CrawlPolicy.from_record(row) for row in records(rows)]
    if name == "anz-v1":
        policies += authority_policies("authorities-v1", directory)
    if len({p.source_id for p in policies}) != len(policies):
        message = "duplicate acquisition identities"
        raise ValueError(message)
    for policy in policies:
        policy.validate()
    return policies


def run_source(
    policy: CrawlPolicy,
    workspace: Path,
    *,
    hub: HubStore | None = None,
    request_budget: int = 20,
    fetch: CapturePort | None = None,
) -> dict[str, object]:
    """Resume a bounded source crawl and optionally publish verified checkpoints.

    Returns:
        The latest crawl, staging and optional remote-publication observations.

    Raises:
        ValueError: Source scope, identity or resource-budget validation fails.
        RuntimeError: The bounded operation cannot produce a valid terminal result.

    """
    crawl_root = workspace / "crawl"
    restored = False
    if hub is not None:
        hub.ensure_public()
        if not (crawl_root / "state.json").exists():
            try:
                restore_source(hub, policy, crawl_root, revision=hub.head())
                restored = True
            except FileNotFoundError as exc:
                # A missing index is first run; missing referenced bytes are corruption.
                if crawl_root.exists() and any(crawl_root.iterdir()):
                    message = "incomplete remote checkpoint; refusing silent restart"
                    raise ValueError(message) from exc
    if request_budget <= 0:
        message = "positive request budget required"
        raise ValueError(message)
    for offset in range(0, request_budget, 5):
        batch = min(request_budget - offset, 5)
        readiness = run_crawl(
            policy, crawl_root, request_budget=batch, fetch=fetch or capture_url
        )
        with TemporaryDirectory(prefix="stage-", dir=workspace) as stage_dir:
            manifest = build_stage(crawl_root, Path(stage_dir))
            publication = (
                publish_stage(hub, Path(stage_dir)) if hub is not None else None
            )
        if readiness["frontier_exhausted"] or offset + batch >= request_budget:
            return {
                "source_id": policy.source_id,
                "restored": restored,
                "readiness": readiness,
                "stage_sha256": string(manifest["sha256"]),
                "publication": publication,
                "gate_b_passed": False,
            }
    message = "validated invocation budget unexpectedly exhausted"
    raise RuntimeError(message)


class Arguments(argparse.Namespace):
    """Typed command-line values after argparse's declared conversions."""

    policies: str | None = None
    collection: str = "au-v1"
    matrix: bool = False
    source_id: str | None = None
    workspace: str = "build/source-run"
    request_budget: int = 20
    capture_only: bool = False


def main(argv: list[str] | None = None) -> int:
    """Run a selected finite acquisition source or emit its workflow matrix.

    Returns:
        Zero on success; a nonzero process status on a blocked or failed operation.

    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policies", help="Explicit legacy or custom policy registry")
    parser.add_argument(
        "--collection",
        choices=("au-v1", "nz-v1", "authorities-v1", "anz-v1"),
        default="au-v1",
    )
    parser.add_argument("--matrix", action="store_true")
    parser.add_argument("--source-id")
    parser.add_argument("--workspace", default="build/source-run")
    parser.add_argument("--request-budget", type=int, default=20)
    parser.add_argument("--capture-only", action="store_true")
    args = parser.parse_args(argv, namespace=Arguments())
    policies = (
        load_policies(Path(args.policies))
        if args.policies
        else load_collection(args.collection)
    )
    if args.matrix:
        if len(policies) > MAX_ACTIONS_MATRIX:
            parser.error(
                "source matrix exceeds runner limit; select a narrower collection"
            )
        sys.stdout.write(
            json.dumps({"source_id": [p.source_id for p in policies]}, sort_keys=True)
            + "\n"
        )
        return 0
    selected = [p for p in policies if p.source_id == args.source_id]
    if len(selected) != 1:
        parser.error("select an exact governed --source-id")
    token = os.environ.get("HF_TOKEN")
    if not token and not args.capture_only:
        sys.stdout.write(
            json.dumps({
                "status": "blocked",
                "reason": "hf_write_credential_required",
                "network_used": False,
            })
            + "\n"
        )
        return 2
    hub = (
        HfStore("edithatogo/au-health-policy-atlas-bronze", token)
        if token and not args.capture_only
        else None
    )
    result = run_source(
        selected[0], Path(args.workspace), hub=hub, request_budget=args.request_budget
    )
    sys.stdout.write(json.dumps(result, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
