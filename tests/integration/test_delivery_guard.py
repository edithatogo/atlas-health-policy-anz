import importlib.util
import subprocess
import zipfile
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("atlas_delivery",ROOT/"scripts/build_delivery.py")
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_empty_archive_and_wrong_project_cannot_be_delivered(tmp_path):
    archive=tmp_path/"empty.zip"
    with zipfile.ZipFile(archive,"w"):
        pass
    with pytest.raises(ValueError,match="empty"):
        module.verify_archive(archive,"a"*40)
    with zipfile.ZipFile(archive,"w") as z:
        z.writestr("something.txt","not a repository")
    with pytest.raises(ValueError,match="incomplete"):
        module.verify_archive(archive,"a"*40)


def test_delivery_rejects_dirty_tree_and_reopens_valid_git(tmp_path):
    repo=tmp_path/"repo"; repo.mkdir()
    def git(*args):
        subprocess.run(["git","-C",str(repo),*args],check=True,capture_output=True,timeout=10)
    git("init","-b","main")
    git("config","user.name","Atlas test fixture")
    git("config","user.email","fixture@example.invalid")
    for name in module.REQUIRED-{".git/HEAD"}:
        path=repo/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text("# fixture\n")
    package=repo/"src/australian_health_policy_atlas"
    (package/"__init__.py").write_text("")
    (package/"cli.py").write_text("def main():\n    return 0\n")
    data=repo/"data/sources/jurisdictions-v1.json";data.parent.mkdir(parents=True,exist_ok=True);data.write_text("{}")
    git("add",".");git("commit","-m","test fixture")
    (repo/"README.md").write_text("changed")
    with pytest.raises(ValueError,match="working-tree"):
        module.build(repo,tmp_path/"out")
    git("add",".");git("commit","-m","fixture change")
    result=module.build(repo,tmp_path/"out")
    assert result["verified"] and result["archive_members"]>10
    assert result["portable_rebuild_identical"]
    assert not result["hosted_ci_verified"]
    with pytest.raises(ValueError,match="commit mismatch"):
        module.verify_archive(tmp_path/"out/australian-health-policy-atlas-recovered.zip","f"*40)
