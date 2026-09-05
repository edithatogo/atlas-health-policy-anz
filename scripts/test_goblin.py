#!/usr/bin/env python3
"""Small Atlas Test-Goblin-compatible quality runner."""

from __future__ import annotations

import argparse
import subprocess
import sys


LANES = {
    "unit": ["pytest", "-q", "tests/unit"],
    "integration": ["pytest", "-q", "tests/integration"],
    "smoke": ["pytest", "-q", "tests/unit/test_source_registry.py", "tests/integration/test_cli.py"],
    "property": ["pytest", "-q", "tests/unit/test_state_machine.py", "tests/unit/test_platinum.py"],
    "contract": ["pytest", "-q", "tests/integration/test_schema_contracts.py"],
    "routine": ["pytest", "-q"],
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("lane", choices=sorted(LANES))
    args = parser.parse_args()
    return subprocess.run([sys.executable, "-m", *LANES[args.lane]], check=False).returncode  # noqa: S603


if __name__ == "__main__":
    raise SystemExit(main())
