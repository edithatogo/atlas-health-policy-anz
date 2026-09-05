#!/usr/bin/env python3
"""Assess a named public staging collection, never infer a Bronze release."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from australian_health_policy_atlas.crawl import CrawlPolicy


import argparse
import json
import os
import shutil
import subprocess  # ruff: ignore[suspicious-subprocess-import] - Bounded argv-only maintenance; no policy text is executed.
from pathlib import Path

from australian_health_policy_atlas.authorities import COLLECTIONS, source_bytes
from australian_health_policy_atlas.hashing import sha256_json
from australian_health_policy_atlas.hub_staging import HfStore, qualify_remote_bronze
from australian_health_policy_atlas.integrity import atomic_json, read_json, sealed
from australian_health_policy_atlas.operations import load_collection
from australian_health_policy_atlas.records import string


class Arguments(argparse.Namespace):
    """Typed values produced by this command's explicit argparse contract."""

    collection: str


def assessment_scope(collection: str) -> tuple[list[CrawlPolicy], str, str]:
    """Bind a named acquisition collection to its own immutable scope identity.

    Returns:
        Validated policies, their scope hash and the denominator description.

    """
    policies = load_collection(collection)
    if collection == "au-v1":
        identity = string(
            read_json(source_bytes("crawl-policies-v1.json"))["census_sha256"]
        )
        kind = "frozen-au-v1-source-surface-census"
    else:
        identity = sha256_json({
            "collection": collection,
            "policies": [p.as_dict() for p in policies],
        })
        kind = "registered-acquisition-profile-scope-not-document-census"
    return policies, identity, kind


def main(argv: list[str] | None = None) -> int:
    """Assess the selected public staging scope and write its evidence receipt.

    Returns:
        Zero on success; a nonzero process status on a blocked or failed operation.

    Raises:
        FileNotFoundError: Git is unavailable to bind the code revision.

    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection", choices=COLLECTIONS, default="au-v1")
    args = parser.parse_args(argv, namespace=Arguments())
    token = os.environ.get("HF_TOKEN")
    if not token:
        print(
            json.dumps({
                "status": "blocked",
                "reason": "hf_credential_required",
                "collection": args.collection,
            })
        )
        return 2
    policies, identity, kind = assessment_scope(args.collection)
    executable = shutil.which("git")
    if executable is None:
        message = "Git executable required to bind the assessment revision"
        raise FileNotFoundError(message)
    code = subprocess.check_output(  # ruff: ignore[subprocess-without-shell-equals-true] - Trusted executable and fixed argv; shell remains disabled.
        [executable, "rev-parse", "HEAD"], text=True, timeout=10
    ).strip()
    result = qualify_remote_bronze(
        HfStore("edithatogo/au-health-policy-atlas-bronze", token),
        policies,
        census_sha256=identity,
        code_revision=code,
    )
    result = sealed({
        **result,
        "collection": args.collection,
        "scope_identity_kind": kind,
        "scope_note": (
            "Named bounded acquisition scope only; not corpus "
            "completeness or a qualified medallion release."
        ),
    })
    atomic_json(Path("build/receipts/bronze-assessment.json"), result)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
