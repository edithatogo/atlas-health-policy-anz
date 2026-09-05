#!/usr/bin/env python3
"""Run bounded, explicitly loaded pytest profiles from the installed lock."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from importlib import metadata
from pathlib import Path

CORE_PLUGINS = (
    "hypothesis",
    "pytest-cov",
    "pytest-timeout",
    "pytest-randomly",
    "pytest-socket",
    "pytest-mock",
    "pytest-subprocess",
    "pytest-httpserver",
    "inline-snapshot",
)
LANES: dict[str, tuple[str, ...]] = {
    "unit": ("tests/unit",),
    "integration": ("tests/integration",),
    "smoke": ("tests/unit/test_source_registry.py", "tests/integration/test_cli.py"),
    "property": ("tests/property",),
    "contract": (
        "tests/integration/test_schema_contracts.py",
        "tests/integration/test_quality_contract.py",
    ),
    "routine": ("tests",),
    "coverage": (
        "tests",
        "--cov=australian_health_policy_atlas",
        "--cov-branch",
        "--cov-report=term-missing",
        "--cov-report=xml",
        "--cov-report=json",
        "--cov-fail-under=95",
    ),
    "parallel": ("tests", "-n", "2", "--dist=loadscope"),
    "benchmark": (
        "tests/benchmarks",
        "--benchmark-only",
        "--benchmark-json=build/quality/benchmark.json",
    ),
    "mutation": (
        "tests/unit/test_state_machine.py",
        "tests/unit/test_verification_errors.py",
        "--gremlins",
    ),
}


class Arguments(argparse.Namespace):
    """Typed CLI arguments, avoiding an Any-based routing boundary."""

    lane: str = "routine"
    seed: int = 20260905


def plugin_arguments(
    distributions: tuple[str, ...],
) -> tuple[list[str], dict[str, str]]:
    """Resolve only allowlisted distribution entry points; never autoload plugins."""
    arguments: list[str] = []
    versions: dict[str, str] = {}
    seen: set[str] = set()
    for name in distributions:
        distribution = metadata.distribution(name)
        entries = sorted(
            (ep for ep in distribution.entry_points if ep.group == "pytest11"),
            key=lambda ep: ep.name,
        )
        if not entries:
            message = f"Required distribution has no pytest entry point: {name}"
            raise RuntimeError(message)
        versions[name] = distribution.version
        for entry in entries:
            if entry.name in seen:
                message = f"Duplicate pytest entry point: {entry.name}"
                raise RuntimeError(message)
            seen.add(entry.name)
            arguments.extend(("-p", entry.name))
    return arguments, versions


def main() -> int:
    """Execute a fixed profile and retain its reproducible plugin/seed receipt."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lane", choices=sorted(LANES))
    parser.add_argument("--seed", type=int, default=20260905)
    args = parser.parse_args(namespace=Arguments())
    lane = args.lane
    seed = args.seed
    selected = CORE_PLUGINS
    if lane == "parallel":
        selected += ("pytest-xdist",)
    if lane == "benchmark":
        selected += ("pytest-benchmark",)
    if lane == "mutation":
        selected += ("pytest-gremlins",)
    plugins, versions = plugin_arguments(selected)
    output = Path("build/quality")
    output.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "pytest",
        "--disable-plugin-autoload",
        *plugins,
        "-q",
        "--disable-socket",
        f"--randomly-seed={seed}",
        *LANES[lane],
    ]
    if lane != "benchmark":
        command.append("--ignore=tests/benchmarks")
    command.append(f"--junitxml={output / (lane + '.xml')}")
    environment = dict(
        os.environ,
        PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
        HF_HUB_OFFLINE="1",
        HF_HUB_DISABLE_TELEMETRY="1",
        DO_NOT_TRACK="1",
        TOKENIZERS_PARALLELISM="false",
        PYTEST_HTTPSERVER_HOST="127.0.0.1",
        ATLAS_HYPOTHESIS_PROFILE="ci",
    )
    environment.pop("PYTEST_ADDOPTS", None)
    receipt: dict[str, object] = {
        "schema_version": 1,
        "lane": lane,
        "seed": seed,
        "python": sys.version,
        "plugins": versions,
        "command": command,
        "network_policy": "python-sockets-denied",
        "security_boundary": "pytest plugin, not an OS/subprocess sandbox",
        "lock_sha256": hashlib.sha256(Path("uv.lock").read_bytes()).hexdigest(),
        "git_sha": os.environ.get("GITHUB_SHA"),
        "status": "executing",
    }
    path = output / (lane + "-receipt.json")
    path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    try:
        completed = subprocess.run(command, env=environment, check=False, timeout=900)  # ruff: ignore[subprocess-without-shell-equals-true] - fixed argv, allowlisted plugins, no shell
        code = completed.returncode
    except subprocess.TimeoutExpired:
        code = 124
    except OSError:
        code = 127
    receipt.update(status="passed" if code == 0 else "failed", returncode=code)
    path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
