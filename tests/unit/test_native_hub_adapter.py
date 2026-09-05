from __future__ import annotations

import pathlib
from types import SimpleNamespace

import pytest

from australian_health_policy_atlas.hub_staging import HfStore


def test_native_hf_adapter_contract_without_network(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    import huggingface_hub as hf
    from huggingface_hub.errors import EntryNotFoundError

    calls = []

    class Api:
        private = False
        sha = "a" * 40
        oid = "b" * 40

        def __init__(self, **kwargs) -> None:
            calls.append(("init", kwargs))

        def create_repo(self, *args, **kwargs) -> None:
            calls.append(("create_repo", kwargs))

        def repo_info(self, *args, **kwargs):
            return SimpleNamespace(private=self.private, sha=self.sha)

        def create_commit(self, **kwargs):
            calls.append(("commit", kwargs))
            return SimpleNamespace(oid=self.oid)

    monkeypatch.setattr(hf, "HfApi", Api)
    target = "edithatogo/au-health-policy-atlas-bronze"
    with pytest.raises(ValueError):
        HfStore(target, "")
    with pytest.raises(ValueError):
        HfStore("other/repo", "fixture")
    store = HfStore(target, "fixture")
    store.ensure_public()
    assert store.head() == "a" * 40
    path = tmp_path / "object"
    path.write_bytes(b"data")

    def download(**kwargs):
        assert kwargs["token"] is False
        assert kwargs["force_download"] is True
        assert kwargs["revision"] == "a" * 40
        return str(path)

    monkeypatch.setattr(hf, "hf_hub_download", download)
    assert store.get("data/object", "a" * 40) == b"data"
    assert (
        store.put({"data/object": path, "meta.json": b"{}"}, parent="a" * 40)
        == "b" * 40
    )
    with pytest.raises(ValueError):
        store.get("data/object", "main")
    monkeypatch.setattr(
        hf,
        "hf_hub_download",
        lambda **_kw: (_ for _ in ()).throw(EntryNotFoundError("absent")),
    )
    with pytest.raises(FileNotFoundError):
        store.get("missing", "a" * 40)
    with pytest.raises(ValueError):
        store.put({})
    store.api.private = True
    with pytest.raises(ValueError):
        store.ensure_public()
    store.api.private = False
    store.api.sha = None
    store.ensure_public()
    store.api.sha = "main"
    with pytest.raises(ValueError):
        store.head()
    store.api.oid = "main"
    with pytest.raises(ValueError):
        store.put({"x": b"x"})
