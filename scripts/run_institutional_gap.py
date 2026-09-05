#!/usr/bin/env python3
"""Compare a local policy against the declared public baseline offline."""

from __future__ import annotations

import argparse
import json

from australian_health_policy_atlas.institutional import run_institutional_gap_analysis


class Arguments(argparse.Namespace):
    """Typed values produced by this command's explicit argparse contract."""

    local_document: str
    public_gold_jsonl: str
    source_id: str
    output_dir: str


def main() -> int:
    """Compare a local policy against the declared public baseline offline.

    Returns:
        Zero on success; a nonzero process status on a blocked or failed operation.

    """
    parser = argparse.ArgumentParser()
    parser.add_argument("local_document")
    parser.add_argument("public_gold_jsonl")
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(namespace=Arguments())
    receipt = run_institutional_gap_analysis(
        local_document=args.local_document,
        local_source_id=args.source_id,
        public_gold_jsonl=args.public_gold_jsonl,
        output_dir=args.output_dir,
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
