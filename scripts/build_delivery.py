#!/usr/bin/env python3
"""Build and reopen a repository ZIP before exposing any delivery artifact.

Requires a clean Git tree. This verifies packaging and Git identity, not
clinical correctness, hosted CI, corpus coverage or publication.
"""

from __future__ import annotations

import argparse
import json
import shutil
import stat
import subprocess  # ruff: ignore[suspicious-subprocess-import] - Bounded argv-only maintenance; no policy text is executed.
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

from australian_health_policy_atlas.distribution import build_zipapp
from australian_health_policy_atlas.hashing import sha256_file
from australian_health_policy_atlas.integrity import atomic_json

PREFIX = "australian-health-policy-atlas"
REQUIRED = {
    "README.md",
    "AGENTS.md",
    "pyproject.toml",
    ".context/project.toml",
    "conductor/registry.toml",
    "src/australian_health_policy_atlas/cli.py",
    ".git/HEAD",
}


class Arguments(argparse.Namespace):
    """Typed values produced by this command's explicit argparse contract."""

    repo: Path
    output_dir: Path


def git_executable() -> str:
    """Resolve Git for the repository-maintenance commands.

    Returns:
        The executable path found in the process environment.

    Raises:
        FileNotFoundError: Git is not installed on the runner.

    """
    executable = shutil.which("git")
    if executable is None:
        message = "Git executable is required for repository delivery"
        raise FileNotFoundError(message)
    return executable


def git(repo: Path, *args: str) -> str:
    """Run a bounded Git command without a shell and return its captured output.

    Returns:
        Captured standard output with trailing whitespace removed.

    Raises:
        ValueError: The supplied data violates the function's documented validation
        contract.

    """
    result = subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true] - Trusted executable and fixed argv; shell remains disabled.
        [git_executable(), "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode:
        message = f"Git command failed ({args[0]}): {result.stderr.strip()}"
        raise ValueError(message)
    return result.stdout.strip()


def verify_archive(path: Path, expected_commit: str) -> dict[str, object]:
    """Reopen a delivery archive and verify its inventory, Git identity and cleanliness.

    Returns:
        Verified commit, archive inventory size, byte length and SHA-256.

    Raises:
        ValueError: The supplied data violates the function's documented validation
        contract.

    """
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if not names or len(set(names)) != len(names):
            message = "empty or duplicate-member repository archive"
            raise ValueError(message)
        if not {f"{PREFIX}/{name}" for name in REQUIRED} <= set(names):
            message = "incomplete repository archive"
            raise ValueError(message)
        for info in archive.infolist():
            part = PurePosixPath(info.filename)
            if (
                part.is_absolute()
                or ".." in part.parts
                or "\\" in info.filename
                or part.parts[0] != PREFIX
                or stat.S_ISLNK(info.external_attr >> 16)
            ):
                message = "unsafe archive member"
                raise ValueError(message)
        if archive.testzip() is not None:
            message = "archive CRC failure"
            raise ValueError(message)
        with tempfile.TemporaryDirectory(prefix="atlas-delivery-verify-") as temp:
            archive.extractall(temp)
            repo = Path(temp) / PREFIX
            observed = git(repo, "rev-parse", "HEAD")
            if observed != expected_commit:
                message = "archive commit mismatch"
                raise ValueError(message)
            git(repo, "fsck", "--full")
            if git(repo, "status", "--porcelain"):
                message = "archived working tree is not clean"
                raise ValueError(message)
    return {
        "verified": True,
        "commit": observed,
        "archive_members": len(names),
        "archive_sha256": sha256_file(path),
        "archive_size_bytes": path.stat().st_size,
    }


def build(repo: Path, output: Path) -> dict[str, object]:
    """Build and independently reverify delivery artifacts from a clean Git tree.

    Returns:
        Artifact verification receipts; no clinical or hosted-CI qualification is
        inferred.

    Raises:
        ValueError: The supplied data violates the function's documented validation
        contract.

    """
    if git(repo, "status", "--porcelain"):
        message = "commit or resolve all working-tree changes before packaging"
        raise ValueError(message)
    commit = git(repo, "rev-parse", "HEAD")
    git(repo, "fsck", "--full")
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="atlas-build-") as temp:
        root = Path(temp)
        clone = root / PREFIX
        result = subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true] - Trusted executable and fixed argv; shell remains disabled.
            [
                git_executable(),
                "clone",
                "--quiet",
                "--no-hardlinks",
                str(repo.resolve()),
                str(clone),
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode:
            message = "clean delivery clone failed"
            raise ValueError(message)
        git(clone, "remote", "remove", "origin")
        archive_path = root / "atlas-repository.zip"
        with zipfile.ZipFile(
            archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
        ) as archive:
            for path in sorted(clone.rglob("*")):
                if path.is_symlink():
                    message = (
                        "repository symlinks require an explicit packaging contract"
                    )
                    raise ValueError(message)
                if path.is_file():
                    archive.write(
                        path, f"{PREFIX}/{path.relative_to(clone).as_posix()}"
                    )
        receipt = verify_archive(archive_path, commit)
        portable = root / "atlas.pyz"
        portable_receipt = build_zipapp(clone, portable)
        repeated = root / "atlas-repeat.pyz"
        build_zipapp(clone, repeated)
        if sha256_file(portable) != sha256_file(repeated):
            message = "portable build is not deterministic"
            raise ValueError(message)
        # All checks completed before copying a deliverable to its final filename.
        final_archive = output / "australian-health-policy-atlas-recovered.zip"
        final_portable = output / "au-health-policy-atlas-recovered.pyz"
        shutil.copyfile(archive_path, final_archive)
        shutil.copyfile(portable, final_portable)
        receipt.update(
            portable=portable_receipt,
            portable_rebuild_identical=True,
            clinical_validation=False,
            hosted_ci_verified=False,
            corpus_release_qualified=False,
        )
        atomic_json(output / "atlas-delivery-receipt.json", receipt)
        (output / "atlas-delivery.sha256").write_text(
            f"{sha256_file(final_archive)}  {final_archive.name}\n"
            f"{sha256_file(final_portable)}  {final_portable.name}\n",
            encoding="utf-8",
        )
        return receipt


def main() -> int:
    """Build and reverify repository and portable delivery artifacts.

    Returns:
        Zero on success; a nonzero process status on a blocked or failed operation.

    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(namespace=Arguments())
    print(json.dumps(build(args.repo, args.output_dir), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
