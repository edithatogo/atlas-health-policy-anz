#!/usr/bin/env python3
"""Build a deterministic source census receipt from the governed seed registry."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from australian_health_policy_atlas.hashing import sha256_json
from australian_health_policy_atlas.source_registry import load_registry


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", default="data/sources/jurisdictions-v1.json")
    parser.add_argument("--output", default="build/census/source-census-v1.json")
    args = parser.parse_args()
    registry = load_registry(args.registry)
    counts: dict[str, int] = {}
    for item in registry["sources"]:
        counts[item["jurisdiction"]] = counts.get(item["jurisdiction"], 0) + 1
    receipt = {
        "schema_version": "1.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "registry_observation_date": registry["observation_date"],
        "source_count": len(registry["sources"]),
        "jurisdiction_counts": dict(sorted(counts.items())),
        "registry_sha256": sha256_json(registry),
        "status": "seed-census-not-complete",
    }
    receipt["receipt_sha256"] = sha256_json(receipt)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
