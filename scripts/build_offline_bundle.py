#!/usr/bin/env python3
"""Package declared files into an independently verifiable offline bundle."""

from __future__ import annotations

import argparse
import json

from australian_health_policy_atlas.offline_bundle import build_bundle


class Arguments(argparse.Namespace):
    """Typed values produced by this command's explicit argparse contract."""

    output_dir: str
    bundle_id: str
    files: list[str]


def main() -> int:
    """Package declared files into an independently verifiable offline bundle.

    Returns:
        Zero on success; a nonzero process status on a blocked or failed operation.

    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--bundle-id", required=True)
    parser.add_argument("files", nargs="+")
    args = parser.parse_args(namespace=Arguments())
    manifest = build_bundle(
        files=args.files, output_dir=args.output_dir, bundle_id=args.bundle_id
    )
    print(json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
