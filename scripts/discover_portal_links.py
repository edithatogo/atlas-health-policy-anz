#!/usr/bin/env python3
"""Discover likely policy documents from a captured portal page."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from australian_health_policy_atlas.discovery import discover_links


class Arguments(argparse.Namespace):
    """Typed values produced by this command's explicit argparse contract."""

    captured_html: str
    base_url: str
    output: str
    include_all: bool


def main() -> int:
    """Report observed source links without asserting document completeness.

    Returns:
        Zero on success; a nonzero process status on a blocked or failed operation.

    """
    parser = argparse.ArgumentParser()
    parser.add_argument("captured_html")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--include-all", action="store_true")
    args = parser.parse_args(namespace=Arguments())
    text = Path(args.captured_html).read_text(encoding="utf-8", errors="replace")
    links = discover_links(text, base_url=args.base_url)
    if not args.include_all:
        links = [item for item in links if item.likely_document]
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "".join(json.dumps(item.__dict__, sort_keys=True) + "\n" for item in links),
        encoding="utf-8",
    )
    print(json.dumps({"links": len(links)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
