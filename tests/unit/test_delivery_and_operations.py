import json
import sys
import subprocess
import zipfile
from pathlib import Path
import pytest

from australian_health_policy_atlas.distribution import build_zipapp
from australian_health_policy_atlas.hashing import sha256_file
from australian_health_policy_atlas import operations
from australian_health_policy_atlas.integrity import atomic_json, read_json
from australian_health_policy_atlas.hub_staging import index_path
from test_crawl_runtime import policy, fetcher
from test_hub_staging_runtime import MemoryHub

REPO = Path(__file__).resolve().parents[2]


def test_zipapp_is_deterministic_and_works_outside_checkout(tmp_path):
    one, two = tmp_path / "first.pyz", tmp_path / "second.pyz"
    result = build_zipapp(REPO, one)
    build_zipapp(REPO, two)
    assert sha256_file(one) == sha256_file(two) == result["sha256"]
    with zipfile.ZipFile(one) as archive:
        assert not any("__pycache__" in n or n.endswith(".pyc") for n in archive.namelist())
        assert any(n.endswith("crawl-policies-v1.json") for n in archive.namelist())
    observed = subprocess.run([sys.executable, str(one), "doctor"],cwd=tmp_path,
        capture_output=True, text=True, check=True, timeout=15)
    assert json.loads(observed.stdout)["status"] == "ok"
    observed = subprocess.run([sys.executable, str(one), "classify-modality", "Nurses must not disclose records."],
        cwd=tmp_path,capture_output=True,text=True,check=True,timeout=15)
    assert json.loads(observed.stdout)["modality"] == "must_not"


def test_bad_package_cannot_build(tmp_path):
    with pytest.raises(ValueError,match="package"):
        build_zipapp(tmp_path,tmp_path/"x.pyz")
    pkg=tmp_path/"src/australian_health_policy_atlas"
    pkg.mkdir(parents=True)
    (pkg/"cli.py").write_text("x=1")
    (pkg/"link.py").symlink_to(pkg/"cli.py")
    with pytest.raises(ValueError,match="registry"):
        build_zipapp(tmp_path,tmp_path/"x.pyz")
    data=tmp_path/"data/sources"
    data.mkdir(parents=True)
    (data/"x.json").symlink_to(pkg/"cli.py")
    with pytest.raises(ValueError,match="symlinks"):
        build_zipapp(tmp_path,tmp_path/"x.pyz")


def test_source_pipeline_can_resume_from_simulated_remote(tmp_path):
    hub=MemoryHub()
    pages={policy().seed_url: b'<a href="/a.pdf">Policy</a>',"https://health.test/a.pdf":b"a"}
    first=operations.run_source(policy(),tmp_path/"first",hub=hub,request_budget=1,fetch=fetcher(pages))
    assert first["readiness"]["counts"]["queued"]==1
    second=operations.run_source(policy(),tmp_path/"second",hub=hub,request_budget=1,fetch=fetcher(pages))
    assert second["restored"] and second["readiness"]["scope_complete"]
    operations.run_source(policy(),tmp_path/"second",hub=hub,request_budget=1,fetch=fetcher(pages))


def test_source_pipeline_without_hub(tmp_path):
    result=operations.run_source(policy(),tmp_path,fetch=fetcher({policy().seed_url:b"x"}))
    assert result["publication"] is None and not result["gate_b_passed"]


def test_missing_remote_object_is_not_first_run(tmp_path):
    hub=MemoryHub()
    operations.run_source(policy(),tmp_path/"first",hub=hub,fetch=fetcher({policy().seed_url:b"x"}))
    ref=read_json(hub.get(index_path(policy()),hub.head()))
    files=hub.snapshots[ref["revision"]]
    files.pop(next(n for n in files if "/cas/" in n))
    with pytest.raises(ValueError,match="checkpoint"):
        operations.run_source(policy(),tmp_path/"second",hub=hub)


def test_operational_cli_has_no_secret_no_network_mode(tmp_path,monkeypatch,capsys):
    policies=REPO/"data/sources/crawl-policies-v1.json"
    monkeypatch.delenv("HF_TOKEN",raising=False)
    assert operations.main(["--policies",str(policies),"--matrix"])==0
    matrix=json.loads(capsys.readouterr().out)
    assert len(matrix["source_id"])==28
    assert operations.main(["--policies",str(policies),"--source-id",matrix["source_id"][0]])==2
    assert json.loads(capsys.readouterr().out)["network_used"] is False
    with pytest.raises(SystemExit):
        operations.main(["--policies",str(policies),"--source-id","not-known"])


def test_operations_cli_dispatch(tmp_path,monkeypatch,capsys):
    policies=REPO/"data/sources/crawl-policies-v1.json"
    source=operations.load_policies(policies)[0]
    monkeypatch.setattr(operations,"run_source",lambda *_a,**_kw: {"done":True})
    assert operations.main(["--policies",str(policies),"--source-id",source.source_id,"--capture-only"])==0
    monkeypatch.setenv("HF_TOKEN","test-placeholder")
    monkeypatch.setattr(operations,"HfStore",lambda *_a:MemoryHub())
    assert operations.main(["--policies",str(policies),"--source-id",source.source_id])==0
    bad=tmp_path/"policies.json"
    atomic_json(bad,{"policies":[]})
    with pytest.raises(ValueError,match="unique"):
        operations.load_policies(bad)
