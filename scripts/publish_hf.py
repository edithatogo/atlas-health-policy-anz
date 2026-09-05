#!/usr/bin/env python3
"""Publish only a hash-verified source-stage package to the public Bronze dataset."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from australian_health_policy_atlas.hub_staging import HfStore, publish_stage


class Arguments(argparse.Namespace):
    """Typed values produced by this command's explicit argparse contract."""

    candidate_dir: str
    repo_id: str


def main() -> int:
    """Publish a qualified candidate and retain remote verification evidence.

    Returns:
        Zero on success; a nonzero process status on a blocked or failed operation.

    """
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate_dir")
    parser.add_argument("--repo-id", default="edithatogo/au-health-policy-atlas-bronze")
    args = parser.parse_args(namespace=Arguments())
    token = os.environ.get("HF_TOKEN")
    if not token:
        print(
            json.dumps({"status": "blocked", "reason": "hf_write_credential_required"})
        )
        return 2
    result = publish_stage(HfStore(args.repo_id, token), Path(args.candidate_dir))
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
