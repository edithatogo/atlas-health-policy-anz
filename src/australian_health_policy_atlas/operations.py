"""Bounded source orchestration, shared by Actions and CLI."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from .crawl import CrawlPolicy, run_crawl
from .hub_staging import HfStore, build_stage, publish_stage, restore_source
from .integrity import read_json


def load_policies(path: Path) -> list[CrawlPolicy]:
    data = read_json(path.read_bytes())
    policies = []
    for row in data["policies"]:
        fields = dict(row)
        fields["allowed_hosts"] = tuple(fields["allowed_hosts"])
        policy = CrawlPolicy(**fields)
        policy.validate()
        policies.append(policy)
    if not policies or len({p.source_id for p in policies}) != len(policies):
        raise ValueError("source policies must be nonempty and unique")
    return policies


def load_collection(name: str = "au-v1", directory: Path | None = None) -> list[CrawlPolicy]:
    """Keep the AU v1 source universe frozen while selecting expanded ANZ sources."""
    from .authorities import COLLECTIONS, authority_policies, source_bytes
    if name not in COLLECTIONS:
        raise ValueError("unknown acquisition collection")
    if name in {"nz-v1", "authorities-v1"}:
        return authority_policies(name, directory)
    rows = read_json(source_bytes("crawl-policies-v1.json", directory))["policies"]
    policies = [CrawlPolicy(**{**row, "allowed_hosts": tuple(row["allowed_hosts"])}) for row in rows]
    if name == "anz-v1":
        policies += authority_policies("authorities-v1", directory)
    if len({p.source_id for p in policies}) != len(policies):
        raise ValueError("duplicate acquisition identities")
    for policy in policies:
        policy.validate()
    return policies


def run_source(policy: CrawlPolicy, workspace: Path, *, hub=None, request_budget: int=20,
               fetch=None) -> dict[str, Any]:
    from .capture import capture_url
    crawl_root = workspace / "crawl"
    restored = False
    if hub is not None:
        hub.ensure_public()
        if not (crawl_root / "state.json").exists():
            try:
                restore_source(hub, policy, crawl_root, revision=hub.head())
                restored = True
            except FileNotFoundError:
                # Missing index is first run, but a missing referenced object is corruption.
                if crawl_root.exists() and any(crawl_root.iterdir()):
                    raise ValueError("incomplete remote checkpoint; refusing silent restart")
    if request_budget <= 0:
        raise ValueError("positive request budget required")
    remaining = request_budget
    publication = None
    while remaining > 0:
        batch = min(remaining, 5)
        readiness = run_crawl(policy, crawl_root, request_budget=batch, fetch=fetch or capture_url)
        with TemporaryDirectory(prefix="stage-", dir=workspace) as stage_dir:
            manifest = build_stage(crawl_root, Path(stage_dir))
            publication = publish_stage(hub, Path(stage_dir)) if hub is not None else None
        remaining -= batch
        if readiness["frontier_exhausted"]:
            break
    return {"source_id": policy.source_id, "restored": restored, "readiness": readiness,
            "stage_sha256": manifest["sha256"], "publication": publication,
            "gate_b_passed": False}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policies", help="Explicit legacy or custom policy registry")
    parser.add_argument("--collection", choices=("au-v1", "nz-v1", "authorities-v1", "anz-v1"), default="au-v1")
    parser.add_argument("--matrix", action="store_true")
    parser.add_argument("--source-id")
    parser.add_argument("--workspace", default="build/source-run")
    parser.add_argument("--request-budget", type=int, default=20)
    parser.add_argument("--capture-only", action="store_true")
    args = parser.parse_args(argv)
    policies = load_policies(Path(args.policies)) if args.policies else load_collection(args.collection)
    if args.matrix:
        if len(policies) > 256:
            parser.error("source matrix exceeds runner limit; select a narrower collection")
        print(json.dumps({"source_id": [p.source_id for p in policies]}, sort_keys=True))
        return 0
    selected = [p for p in policies if p.source_id == args.source_id]
    if len(selected) != 1:
        parser.error("select an exact governed --source-id")
    token = os.environ.get("HF_TOKEN")
    if not token and not args.capture_only:
        print(json.dumps({"status": "blocked", "reason": "hf_write_credential_required", "network_used": False}))
        return 2
    hub = HfStore("edithatogo/au-health-policy-atlas-bronze", token) if token and not args.capture_only else None
    result = run_source(selected[0], Path(args.workspace), hub=hub, request_budget=args.request_budget)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
