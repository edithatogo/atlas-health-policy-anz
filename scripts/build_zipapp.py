#!/usr/bin/env python3
"""Build a dependency-free portable Atlas zipapp from the stdlib core."""

from __future__ import annotations

import argparse
import zipapp
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="dist/au-health-policy-atlas.pyz")
    args = parser.parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    zipapp.create_archive(
        "src",
        target=output,
        main="australian_health_policy_atlas.cli:main",
        interpreter="/usr/bin/env python3",
        compressed=True,
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
