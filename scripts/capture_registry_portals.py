#!/usr/bin/env python3
"""Capture every governed seed portal into content-addressed storage."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from australian_health_policy_atlas.capture import capture_url
from australian_health_policy_atlas.hashing import sha256_json
from australian_health_policy_atlas.source_registry import load_registry


class Arguments(argparse.Namespace):
    """Typed values produced by this command's explicit argparse contract."""

    registry: str
    output_dir: str
    continue_on_error: bool


def main() -> int:
    """Capture the selected registry source portals with bounded requests.

    Returns:
        Zero on success; a nonzero process status on a blocked or failed operation.

    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", default="data/sources/jurisdictions-v1.json")
    parser.add_argument("--output-dir", default="build/portal-capture")
    parser.add_argument("--continue-on-error", action="store_true")
    args = parser.parse_args(namespace=Arguments())
    registry = load_registry(args.registry)
    root = Path(args.output_dir)
    cas = root / "cas"
    receipts: list[dict[str, object]] = []
    failures: list[dict[str, str]] = []
    for source in registry["sources"]:
        source_id = source["source_id"]
        try:
            receipt = capture_url(
                source["url"],
                cas_root=cas,
                receipt_path=root / "receipts" / f"{source_id}.json",
            )
            row = receipt.as_dict()
            row["source_id"] = source_id
            row["jurisdiction"] = source["jurisdiction"]
            receipts.append(row)
        except Exception as exc:
            failures.append({
                "source_id": source_id,
                "error_type": type(exc).__name__,
                "message": str(exc),
            })
            if not args.continue_on_error:
                raise
    summary: dict[str, object] = {
        "schema_version": "1.0",
        "captured": len(receipts),
        "failed": len(failures),
        "receipts": receipts,
        "failures": failures,
    }
    summary["summary_sha256"] = sha256_json(summary)
    root.mkdir(parents=True, exist_ok=True)
    (root / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps({"captured": len(receipts), "failed": len(failures)}, sort_keys=True)
    )
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
