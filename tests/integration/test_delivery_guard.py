from __future__ import annotations

import pathlib
import subprocess  # ruff: ignore[suspicious-subprocess-import] - Bounded argv-only maintenance; no policy text is executed.
import zipfile
from pathlib import Path

import pytest
from scripts import build_delivery as module

from australian_health_policy_atlas.records import integer

ROOT = Path(__file__).resolve().parents[2]


def test_empty_archive_and_wrong_project_cannot_be_delivered(
    tmp_path: pathlib.Path,
) -> None:
    archive = tmp_path / "empty.zip"
    with zipfile.ZipFile(archive, "w"):
        pass
    with pytest.raises(ValueError, match="empty"):
        module.verify_archive(archive, "a" * 40)
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("something.txt", "not a repository")
    with pytest.raises(ValueError, match="incomplete"):
        module.verify_archive(archive, "a" * 40)


def test_delivery_rejects_dirty_tree_and_reopens_valid_git(
    tmp_path: pathlib.Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    def git(*args: str) -> None:
        subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true] - Trusted executable and fixed argv; shell remains disabled.
            [module.git_executable(), "-C", str(repo), *args],
            check=True,
            capture_output=True,
            timeout=10,
        )

    git("init", "-b", "main")
    git("config", "user.name", "Atlas test fixture")
    git("config", "user.email", "fixture@example.invalid")
    for name in module.REQUIRED - {".git/HEAD"}:
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# fixture\n")
    package = repo / "src/australian_health_policy_atlas"
    (package / "__init__.py").write_text("")
    (package / "cli.py").write_text("def main():\n    return 0\n")
    data = repo / "data/sources/jurisdictions-v1.json"
    data.parent.mkdir(parents=True, exist_ok=True)
    data.write_text("{}")
    git("add", ".")
    git("commit", "-m", "test fixture")
    (repo / "README.md").write_text("changed")
    with pytest.raises(ValueError, match="working-tree"):
        module.build(repo, tmp_path / "out")
    git("add", ".")
    git("commit", "-m", "fixture change")
    result = module.build(repo, tmp_path / "out")
    assert result["verified"]
    assert integer(result["archive_members"]) > 10
    assert result["portable_rebuild_identical"]
    assert not result["hosted_ci_verified"]
    with pytest.raises(ValueError, match="commit mismatch"):
        module.verify_archive(
            tmp_path / "out/australian-health-policy-atlas-recovered.zip", "f" * 40
        )
