#!/usr/bin/env python3
"""Check all offline bundle payloads and report their integrity failures."""

from __future__ import annotations

import argparse
import json

from australian_health_policy_atlas.offline_bundle import verify_bundle


class Arguments(argparse.Namespace):
    """Typed values produced by this command's explicit argparse contract."""

    bundle_dir: str


def main() -> int:
    """Check all offline bundle payloads and report their integrity failures.

    Returns:
        Zero on success; a nonzero process status on a blocked or failed operation.

    """
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle_dir")
    args = parser.parse_args(namespace=Arguments())
    ok, failures = verify_bundle(args.bundle_dir)
    print(json.dumps({"verified": ok, "failures": failures}, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
