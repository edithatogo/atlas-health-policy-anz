#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from australian_health_policy_atlas.institutional import run_institutional_gap_analysis


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("local_document")
    parser.add_argument("public_gold_jsonl")
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
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
