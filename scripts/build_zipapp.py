#!/usr/bin/env python3
"""Build the deterministic portable Atlas application, excluding caches."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from australian_health_policy_atlas.distribution import build_zipapp


class Arguments(argparse.Namespace):
    """Typed values produced by this command's explicit argparse contract."""

    output: str


def main() -> int:
    """Build the deterministic portable command-line application.

    Returns:
        Zero on success; a nonzero process status on a blocked or failed operation.

    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="dist/au-health-policy-atlas.pyz")
    args = parser.parse_args(namespace=Arguments())
    result = build_zipapp(Path(__file__).resolve().parents[1], Path(args.output))
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
