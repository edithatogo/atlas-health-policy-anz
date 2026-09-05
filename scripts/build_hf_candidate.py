#!/usr/bin/env python3
"""Build a local Hugging Face Bronze publication candidate from a manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from australian_health_policy_atlas.publication import build_bronze_hf_candidate
from australian_health_policy_atlas.records import decode_json, record


class Arguments(argparse.Namespace):
    """Typed values produced by this command's explicit argparse contract."""

    manifest: str
    output_dir: str
    dataset_id: str


def main() -> int:
    """Assemble a local Hugging Face candidate from the declared Bronze manifest.

    Returns:
        Zero on success; a nonzero process status on a blocked or failed operation.

    """
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--dataset-id", default="edithatogo/au-health-policy-atlas-bronze"
    )
    args = parser.parse_args(namespace=Arguments())
    manifest = record(decode_json(Path(args.manifest).read_text(encoding="utf-8")))
    receipt = build_bronze_hf_candidate(
        manifest, output_dir=args.output_dir, dataset_id=args.dataset_id
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
