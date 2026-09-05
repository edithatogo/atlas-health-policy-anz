#!/usr/bin/env python3
"""Enforce whole-repository static checks; retain failures, never baseline them away."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path

CHECKS: dict[str, tuple[str, ...]] = {
    "ruff": ("ruff", "check", "--output-format=json", "src", "scripts", "tests"),
    "format": ("ruff", "format", "--check", "src", "scripts", "tests"),
    "basedpyright": ("basedpyright", "--outputjson"),
    "ty": ("ty", "check", "src", "scripts", "tests"),
}


class Arguments(argparse.Namespace):
    """Typed, closed-set check selection."""

    checker: str = "ruff"


def main() -> int:
    """Run the selected non-compensatory check and write a failure-aware receipt."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checker", choices=sorted(CHECKS))
    args = parser.parse_args(namespace=Arguments())
    checker = args.checker
    command = CHECKS[checker]
    output = Path("build/quality")
    output.mkdir(parents=True, exist_ok=True)
    distribution = "ruff" if checker == "format" else checker
    receipt: dict[str, object] = {
        "checker": checker,
        "tool_version": version(distribution),
        "python": sys.version,
        "command": command,
        "git_sha": os.environ.get("GITHUB_SHA"),
        "lock_sha256": hashlib.sha256(Path("uv.lock").read_bytes()).hexdigest(),
        "scope": ["src", "scripts", "tests"],
        "baseline_suppression": False,
    }
    try:
        completed = subprocess.run(
            command, capture_output=True, text=True, check=False, timeout=600
        )  # ruff: ignore[subprocess-without-shell-equals-true] - closed-set argv and no shell
        code, stdout, stderr = completed.returncode, completed.stdout, completed.stderr
    except subprocess.TimeoutExpired:
        code, stdout, stderr = 124, "", "Static analysis exceeded its time budget."
    except OSError:
        code, stdout, stderr = 127, "", "Static-analysis tool could not be executed."
    (output / (checker + ".stdout")).write_text(stdout, encoding="utf-8")
    (output / (checker + ".stderr")).write_text(stderr, encoding="utf-8")
    receipt.update(returncode=code, status="passed" if code == 0 else "failed")
    (output / (checker + "-receipt.json")).write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(receipt, indent=2))
    print((stdout + stderr)[-6000:])
    return code


if __name__ == "__main__":
    raise SystemExit(main())
