#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from australian_health_policy_atlas.offline_bundle import verify_bundle


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle_dir")
    args = parser.parse_args()
    ok, failures = verify_bundle(args.bundle_dir)
    print(json.dumps({"verified": ok, "failures": failures}, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
