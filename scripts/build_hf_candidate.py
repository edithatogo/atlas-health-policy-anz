#!/usr/bin/env python3
"""Build a local Hugging Face Bronze publication candidate from a manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from australian_health_policy_atlas.publication import build_bronze_hf_candidate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--dataset-id", default="edithatogo/au-health-policy-atlas-bronze")
    args = parser.parse_args()
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    receipt = build_bronze_hf_candidate(manifest, output_dir=args.output_dir, dataset_id=args.dataset_id)
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
