#!/usr/bin/env python3
"""Publish only a hash-verified source-stage package to the public Bronze dataset."""
import argparse
import json
import os
from pathlib import Path
from australian_health_policy_atlas.hub_staging import HfStore, publish_stage


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate_dir")
    parser.add_argument("--repo-id", default="edithatogo/au-health-policy-atlas-bronze")
    args = parser.parse_args()
    token = os.environ.get("HF_TOKEN")
    if not token:
        print(json.dumps({"status":"blocked","reason":"hf_write_credential_required"}))
        return 2
    result = publish_stage(HfStore(args.repo_id, token), Path(args.candidate_dir))
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
