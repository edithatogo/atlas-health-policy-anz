from dataclasses import replace
from pathlib import Path
import pytest

from australian_health_policy_atlas.hub_staging import (build_stage, verify_stage, publish_stage,
    restore_source, _remote_stage, index_path, ConcurrentUpdateError)
from australian_health_policy_atlas.integrity import read_json, sealed, atomic_json, canonical_json_bytes
from australian_health_policy_atlas.hashing import sha256_bytes
from test_crawl_runtime import policy
from test_hub_staging_runtime import MemoryHub, stage


@pytest.mark.parametrize("mutation",["kind","duplicates","identity","unreferenced"])
def test_valid_selfhash_does_not_override_contract(tmp_path,mutation):
    source=stage(tmp_path)
    manifest=read_json((source/"manifest.json").read_bytes())
    if mutation=="kind": manifest["kind"]="medallion-release"
    if mutation=="duplicates": manifest["files"].append(dict(manifest["files"][0]))
    if mutation=="identity": manifest["files"][0]["sha256"]="invalid"
    if mutation=="unreferenced":
        (source/"unreferenced.txt").write_bytes(b"x")
        manifest["files"].append({"path":"unreferenced.txt","sha256":sha256_bytes(b"x"),"size_bytes":1})
    atomic_json(source/"manifest.json",sealed(manifest))
    with pytest.raises(ValueError): verify_stage(source)


def test_nested_stage_is_forbidden(tmp_path):
    stage(tmp_path)
    with pytest.raises(ValueError,match="outside"):
        build_stage(tmp_path/"crawl",tmp_path/"crawl/nested")


@pytest.mark.parametrize("mutation",["revision","identity","source","hash"])
def test_remote_reference_validation(tmp_path,mutation):
    hub=MemoryHub()
    observation=publish_stage(hub,stage(tmp_path))
    reference=dict(observation["reference"])
    if mutation=="revision": reference["revision"]="main"
    if mutation=="identity": reference["manifest_sha256"]="bad"
    if mutation=="source": reference["source_id"]="../wrong"
    if mutation=="hash":
        prefix=f"staging/{reference['source_id']}/{reference['manifest_sha256']}"
        manifest=read_json(hub.snapshots[reference["revision"]][prefix+"/manifest.json"])
        manifest["extra"]="changed"
        hub.snapshots[reference["revision"]][prefix+"/manifest.json"]=canonical_json_bytes(sealed(manifest))
    with pytest.raises(ValueError): _remote_stage(hub,sealed(reference),tmp_path/"restore")


def test_nonempty_restore_refused(tmp_path):
    hub=MemoryHub(); observation=publish_stage(hub,stage(tmp_path))
    with pytest.raises(ValueError,match="empty"):
        _remote_stage(hub,observation["reference"],tmp_path/"stage")


def test_conflicting_generation_is_refused(tmp_path):
    source=stage(tmp_path);hub=MemoryHub();publish_stage(hub,source)
    previous=read_json(hub.get(index_path(policy()),hub.head()))
    previous["manifest_sha256"]="f"*64
    hub.put({index_path(policy()):canonical_json_bytes(sealed(previous))})
    with pytest.raises(ValueError,match="conflicting"):
        publish_stage(hub,source)


def test_source_scope_cannot_be_substituted(tmp_path):
    hub=MemoryHub();publish_stage(hub,stage(tmp_path))
    other=replace(policy(),max_depth=3)
    hub.put({index_path(other):hub.get(index_path(policy()),hub.head())})
    with pytest.raises(ValueError,match="wrong scope"):
        restore_source(hub,other,tmp_path/"restore",revision=hub.head())


def test_pointer_tamper_detected_after_commit(tmp_path):
    class Hub(MemoryHub):
        def get(self,path,revision):
            value=super().get(path,revision)
            return b"altered" if "staging/index/" in path else value
    with pytest.raises(ValueError,match="pointer byte"):
        publish_stage(Hub(),stage(tmp_path))


def test_concurrent_source_change_is_not_overwritten(tmp_path):
    class Hub(MemoryHub):
        def put(self,files,*,parent=None):
            result=super().put(files,parent=parent)
            if any("/manifest.json" in n for n in files):
                super().put({index_path(policy()):b'{"a":"concurrent"}'})
            return result
    with pytest.raises(ValueError,match="source pointer changed"):
        publish_stage(Hub(),stage(tmp_path))


@pytest.mark.parametrize("conflicts",[1,3])
def test_conditional_commit_conflicts_retry_boundedly(tmp_path,conflicts):
    class Hub(MemoryHub):
        failures=0
        def put(self,files,*,parent=None):
            if parent is not None and self.failures<conflicts:
                self.failures+=1
                raise ConcurrentUpdateError("fixture conflict")
            return super().put(files,parent=parent)
    hub=Hub()
    if conflicts==3:
        with pytest.raises(ConcurrentUpdateError):publish_stage(hub,stage(tmp_path))
        assert hub.failures==3
    else:
        assert publish_stage(hub,stage(tmp_path))["remote_bytes_verified"]
