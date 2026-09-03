#!/usr/bin/env python3
"""Upload a prepared public dataset candidate and verify the remote revision."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate_dir")
    parser.add_argument("--repo-id", required=True)
    parser.add_argument("--revision", default="main")
    args = parser.parse_args()
    token = os.environ.get("HF_TOKEN")
    if not token:
        raise SystemExit("HF_TOKEN is required")
    try:
        from huggingface_hub import HfApi  # type: ignore[import-not-found]
    except ImportError as exc:
        raise SystemExit("Install the qualified publication dependency group containing huggingface_hub") from exc
    api = HfApi(token=token)
    api.create_repo(args.repo_id, repo_type="dataset", exist_ok=True, private=False)
    commit = api.upload_folder(
        folder_path=args.candidate_dir,
        repo_id=args.repo_id,
        repo_type="dataset",
        revision=args.revision,
        commit_message="Publish Atlas dataset candidate",
    )
    info = api.repo_info(args.repo_id, repo_type="dataset", revision=commit.oid)
    receipt = {
        "schema_version": "1.0",
        "repo_id": args.repo_id,
        "requested_revision": args.revision,
        "remote_commit": commit.oid,
        "remote_sha": info.sha,
        "verified": info.sha == commit.oid,
    }
    path = Path(args.candidate_dir) / "remote-publication-receipt.json"
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
