"""Temporary checksum-gated transport for already reviewed, locally tested edits."""
from __future__ import annotations

import base64
import hashlib
import json
import lzma
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

REPO = "edithatogo/atlas-health-policy-anz"
BRANCH = "fix/strict-type-quality"
SOURCE = "99140d55c9d570abdf746a7d1f8de07dd03e7133"
PATCH_HASH = "6881e47adfce8455fee746f2de866bda375b58aff7a1386b23b832aaf282f3f6"
COMPRESSED_HASH = "e370b5bf1d5bf2c0fb1da08476a5a85b32fd60f7b6c5a634185dedb914aa5e27"
INVENTORY_HASH = "4d3542cd8f7245fb9e5b8bfc9f7557bcf94caeb48ab78eb7142f1734a7e65a26"
CONTRACTS = {
    "pyproject.toml": "69ca7eab1fdd3d3231758ff93d5e44409ba132401e4d89c3d7b67a9147393099",
    "uv.lock": "8d19325b11a134540c41566bd37a8b36dabba1b729d05e072f18ae3503219d60",
}
ROOTS = ("src", "scripts", "tests", "quality", "conductor")
PARTS = (
    "9ec71842d61e1ee5d4fa44eb4ad26aef22306b14",
    "78af7785aecd969dcab9fa270fbb02f742b758a1",
    "46eee44f5639898d4bc5e10c4dedebb75e3344e6",
    "42143c643df8d3018b192280d175539aaa4033ae",
    "2e747b3dcb11b719d836baab859a73c4049e9bfb",
    "23ef4374f23a2490f84e24b71c391694c8f767ee",
    "76a382007a44637e80351532da9f6781665f92dc",
    "50690b01f3b0b703ea6f5d0a3e765395d24e69ed",
    "1d3f38527e5222eceb05a23cc22c2e70a30669f1",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def git(*args, data=None):
    return subprocess.check_output(["git", *args], input=data)


def guard():
    require(os.environ.get("GITHUB_REPOSITORY") == REPO, "Unexpected repository")
    require(os.environ.get("GITHUB_REF") == "refs/heads/" + BRANCH, "Unexpected ref")
    require(git("branch", "--show-current").decode().strip() == BRANCH, "Unexpected checkout")
    for path, digest in CONTRACTS.items():
        require(hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest,
                "Quality configuration or lock changed: " + path)


def verify_inventory():
    paths = git("diff", "--cached", "--name-only", "-z").decode().split("\0")
    inventory = []
    for path in filter(None, paths):
        require(path.split("/")[0] in ROOTS and ".." not in Path(path).parts,
                "Unexpected staged path: " + path)
        require(Path(path).is_file() and not Path(path).is_symlink(), "Unsafe source path")
        fields = git("ls-files", "--stage", "--", path).decode().split()
        require(fields[0] in ("100644", "100755") and fields[2] == "0", "Invalid index entry")
        inventory.append([path, fields[0], fields[1]])
    encoded = json.dumps(inventory, separators=(",", ":")).encode()
    require(len(inventory) == 104 and hashlib.sha256(encoded).hexdigest() == INVENTORY_HASH,
            "Reviewed source inventory mismatch")
    require(not git("diff", "--name-only", "--", *ROOTS), "Unstaged source changes")


def apply():
    guard()
    require(not git("status", "--porcelain", "--untracked-files=no"), "Dirty tracked checkout")
    subprocess.run(["git", "merge-base", "--is-ancestor", SOURCE, "HEAD"], check=True)
    require(not git("diff", SOURCE, "HEAD", "--", *ROOTS, *CONTRACTS),
            "Source changed since reviewed baseline; refusing to overwrite")
    chunks = []
    for i, expected in enumerate(PARTS, start=1):
        path = Path(f".strict-repair/part-{i:02d}.xz")
        require(path.is_file() and not path.is_symlink(), "Unsafe transport part")
        require(path.stat().st_size == (8000 if i < 9 else 960), "Part size mismatch")
        raw = path.read_bytes()
        require(git("hash-object", str(path)).decode().strip() == expected, "Part identity mismatch")
        chunks.append(raw)
    compressed = b"".join(chunks)
    require(len(compressed) == 64960 and hashlib.sha256(compressed).hexdigest() == COMPRESSED_HASH,
            "Compressed transport mismatch")
    decoder = lzma.LZMADecompressor(memlimit=128 * 1024 * 1024)
    patch = decoder.decompress(compressed, max_length=362275)
    require(decoder.eof and not decoder.unused_data and len(patch) == 362274,
            "Bounded decompression failed")
    require(hashlib.sha256(patch).hexdigest() == PATCH_HASH, "Reviewed patch mismatch")
    git("apply", "--check", "--index", "--unidiff-zero", data=patch)
    git("apply", "--index", "--unidiff-zero", data=patch)
    verify_inventory()
    guard()
    git("diff", "--cached", "--check")
    print("Applied and verified all 104 reviewed source paths; contracts unchanged.")


def commit():
    guard()
    verify_inventory()
    checks = {}
    for name in ("ruff", "format", "basedpyright", "ty", "coverage", "parallel", "benchmark"):
        path = Path("build/quality") / (name + "-receipt.json")
        result = json.loads(path.read_text())
        require(result.get("status") == "passed" and result.get("returncode") == 0,
                "Required gate failed: " + name)
        checks[name] = {"status": "passed", "receipt_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    suites = ET.parse("build/quality/coverage.xml").getroot().iter("testsuite")
    totals = {key: 0 for key in ("tests", "failures", "errors", "skipped")}
    for suite in suites:
        for key in totals:
            totals[key] += int(suite.get(key, "0"))
    require(totals == {"tests": 348, "failures": 0, "errors": 0, "skipped": 0},
            "Unexpected test result")
    coverage = json.loads(Path("coverage.json").read_text())["totals"]
    require(coverage["percent_covered"] >= 95, "Coverage minimum not met")
    receipt = {"schema_version": 1, "kind": "hosted-strict-remediation", "source_base": SOURCE,
               "repair_parent": git("rev-parse", "HEAD").decode().strip(),
               "repository": REPO, "branch": BRANCH, "tracks": ["T00", "T06", "T07"],
               "patch_sha256": PATCH_HASH, "inventory_sha256": INVENTORY_HASH,
               "reviewed_paths": 104, "contracts": CONTRACTS, "checks": checks,
               "tests": totals, "coverage_totals": coverage, "python": sys.version,
               "workflow_run_id": os.environ.get("GITHUB_RUN_ID"),
               "config_and_lock_unchanged": True, "hf_writes": 0,
               "original_policy_payloads_captured": 0, "medallion_promotion": False,
               "normal_final_pr_workflows": "pending; this is the repair-run receipt"}
    Path("quality/strict-remediation-hosted.json").write_text(json.dumps(receipt, indent=2) + "\n")
    git("config", "user.name", "github-actions[bot]")
    git("config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    git("add", "quality/strict-remediation-hosted.json")
    require(not git("diff", "--cached", "--name-only", "--", ".github"), "Unexpected workflow edits")
    git("diff", "--cached", "--check")
    git("commit", "-m", "refactor: eliminate strict lint and typing debt with validated data boundaries")
    auth = base64.b64encode(("x-access-token:" + os.environ["GH_TOKEN"]).encode()).decode()
    print("::add-mask::" + auth, flush=True)
    environment = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_CONFIG_COUNT="1",
                       GIT_CONFIG_KEY_0="http.https://github.com/.extraheader",
                       GIT_CONFIG_VALUE_0="AUTHORIZATION: basic " + auth)
    subprocess.run(["git", "push", "origin", "HEAD:refs/heads/" + BRANCH], env=environment, check=True)
    print("Verified repair committed:", git("rev-parse", "HEAD").decode().strip())


if __name__ == "__main__":
    require(len(sys.argv) == 2 and sys.argv[1] in ("apply", "commit"), "Expected apply or commit")
    (apply if sys.argv[1] == "apply" else commit)()
