#!/usr/bin/env python3
"""Prepare a local/sensitive document without network access."""

from __future__ import annotations

import argparse
import json

from australian_health_policy_atlas.local_runner import prepare_local_document


class Arguments(argparse.Namespace):
    """Typed values produced by this command's explicit argparse contract."""

    document: str
    source_id: str
    output_dir: str


def main() -> int:
    """Prepare a local document without uploading its text or derived features.

    Returns:
        Zero on success; a nonzero process status on a blocked or failed operation.

    """
    parser = argparse.ArgumentParser()
    parser.add_argument("document")
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(namespace=Arguments())
    receipt = prepare_local_document(
        args.document, source_id=args.source_id, output_dir=args.output_dir
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
