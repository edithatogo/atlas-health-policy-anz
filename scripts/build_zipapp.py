#!/usr/bin/env python3
"""Build the deterministic portable Atlas application, excluding caches."""
from pathlib import Path
import argparse
import json
from australian_health_policy_atlas.distribution import build_zipapp


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="dist/au-health-policy-atlas.pyz")
    args = parser.parse_args()
    result = build_zipapp(Path(__file__).resolve().parents[1], Path(args.output))
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
