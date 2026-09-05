#!/usr/bin/env python3
"""Prepare a local/sensitive document without network access."""

from __future__ import annotations

import argparse
import json

from australian_health_policy_atlas.local_runner import prepare_local_document


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("document")
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    receipt = prepare_local_document(
        args.document, source_id=args.source_id, output_dir=args.output_dir
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
