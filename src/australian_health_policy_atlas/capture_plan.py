"""Compile a secret-free, identity-bound acquisition plan before remote operations."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from .hashing import sha256_json
from .integrity import atomic_json, sealed
from .operations import MAX_ACTIONS_MATRIX, load_collection
from .packet_ingestion import require_packet

if TYPE_CHECKING:
    from .crawl import CrawlPolicy

MAX_FRONTIER_ATTEMPTS = 5120


def compile_plan(
    policies: list[CrawlPolicy], collection: str, request_budget: int
) -> dict[str, object]:
    """Bind the matrix and invocation budget to exact validated source policies.

    Returns:
        A deterministic, non-executing plan. Budgets count frontier attempts, not
        HTTP redirects, remote checkpoint downloads or total billed runner time.
        A plan and exhausted frontier never assert document-corpus completeness.

    """
    require_packet(bool(collection), "explicit collection identity required")
    require_packet(
        type(request_budget) is int and request_budget > 0,
        "positive integer request budget required",
    )
    require_packet(
        0 < len(policies) <= MAX_ACTIONS_MATRIX, "invalid workflow matrix size"
    )
    require_packet(
        len(policies) * request_budget <= MAX_FRONTIER_ATTEMPTS,
        "aggregate frontier budget exceeded",
    )
    for policy in policies:
        policy.validate()
    ordered = sorted(policies, key=lambda policy: policy.source_id)
    identities = [policy.source_id for policy in ordered]
    require_packet(len(set(identities)) == len(identities), "duplicate plan source")
    return sealed({
        "schema_version": "1.0",
        "kind": "bounded-acquisition-plan",
        "collection": collection,
        "matrix": {"source_id": identities},
        "source_count": len(ordered),
        "policies_sha256": sha256_json([policy.as_dict() for policy in ordered]),
        "source_policy_hashes": {
            policy.source_id: sha256_json(policy.as_dict()) for policy in ordered
        },
        "frontier_attempts_per_source": request_budget,
        "maximum_frontier_attempts": len(ordered) * request_budget,
        "budget_scope": "frontier_attempts_not_redirects_or_hf_transfers",
        "network_used": False,
        "capture_executed": False,
        "corpus_completeness_claimed": False,
        "not_medallion_release": True,
        "gate_b_passed": False,
    })


class Arguments(argparse.Namespace):
    """Typed command-line selections for the offline plan compiler."""

    collection: str = "anz-v1"
    request_budget: int = 20
    receipt: Path = Path("build/capture-plan.json")


def main(argv: list[str] | None = None) -> int:
    """Write the plan receipt and emit only a validated workflow matrix to stdout.

    Returns:
        Zero after deterministic validation. Invalid budgets fail before file writes.

    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--collection",
        choices=("au-v1", "nz-v1", "authorities-v1", "anz-v1"),
        default="anz-v1",
    )
    parser.add_argument("--request-budget", type=int, default=20)
    parser.add_argument("--receipt", type=Path, default=Path("build/capture-plan.json"))
    args = parser.parse_args(argv, namespace=Arguments())
    result = compile_plan(
        load_collection(args.collection), args.collection, args.request_budget
    )
    atomic_json(args.receipt, result)
    sys.stdout.write(json.dumps(result["matrix"], sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
