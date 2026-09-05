#!/usr/bin/env python3
"""Assess exact public source staging; never substitute this for a Bronze release."""
import json
import os
import subprocess
from pathlib import Path
from australian_health_policy_atlas.operations import load_policies
from australian_health_policy_atlas.hub_staging import HfStore, qualify_remote_bronze
from australian_health_policy_atlas.integrity import atomic_json, read_json


def main() -> int:
    token=os.environ.get("HF_TOKEN")
    if not token:
        print(json.dumps({"status":"blocked","reason":"hf_credential_required"}))
        return 2
    policies=Path("data/sources/crawl-policies-v1.json")
    code=subprocess.check_output(["git","rev-parse","HEAD"],text=True,timeout=10).strip()
    result=qualify_remote_bronze(HfStore("edithatogo/au-health-policy-atlas-bronze",token),
        load_policies(policies),census_sha256=read_json(policies.read_bytes())["census_sha256"],code_revision=code)
    atomic_json(Path("build/receipts/bronze-assessment.json"),result)
    print(json.dumps(result,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
