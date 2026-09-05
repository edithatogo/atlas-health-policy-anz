from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pathlib


from types import SimpleNamespace

import huggingface_hub as hf
import pytest
from huggingface_hub.errors import EntryNotFoundError

from australian_health_policy_atlas.hub_staging import HfStore
from tests.support import ignoring_arguments


def test_native_hf_adapter_contract_without_network(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:

    calls: list[tuple[str, dict[str, object]]] = []

    class Api:
        private = False
        sha: str | None = "a" * 40
        oid = "b" * 40

        def __init__(self, **kwargs: object) -> None:
            calls.append(("init", kwargs))

        @staticmethod
        def create_repo(*_args: object, **kwargs: object) -> None:
            calls.append(("create_repo", kwargs))

        def repo_info(self, *_args: object, **_kwargs: object) -> SimpleNamespace:
            return SimpleNamespace(private=self.private, sha=self.sha)

        def create_commit(self, **kwargs: object) -> SimpleNamespace:
            calls.append(("commit", kwargs))
            return SimpleNamespace(oid=self.oid)

    api = Api()
    monkeypatch.setattr(hf, "HfApi", ignoring_arguments(lambda: api))
    target = "edithatogo/au-health-policy-atlas-bronze"
    with pytest.raises(ValueError, match="explicit Atlas Bronze target"):
        HfStore(target, "")
    with pytest.raises(ValueError, match="explicit Atlas Bronze target"):
        HfStore("other/repo", "fixture")
    store = HfStore(target, "fixture")
    store.ensure_public()
    assert store.head() == "a" * 40
    path = tmp_path / "object"
    path.write_bytes(b"data")

    def download(**kwargs: object) -> str:
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
    with pytest.raises(ValueError, match="pinned commit"):
        store.get("data/object", "main")
    monkeypatch.setattr(
        hf,
        "hf_hub_download",
        ignoring_arguments(lambda: (_ for _ in ()).throw(EntryNotFoundError("absent"))),
    )
    with pytest.raises(FileNotFoundError):
        store.get("missing", "a" * 40)
    with pytest.raises(ValueError, match="bounded Hub transaction"):
        store.put({})
    api.private = True
    with pytest.raises(ValueError, match="private dataset"):
        store.ensure_public()
    api.private = False
    api.sha = None
    store.ensure_public()
    api.sha = "main"
    with pytest.raises(ValueError, match="immutable commit"):
        store.head()
    api.oid = "main"
    with pytest.raises(ValueError, match="immutable publication"):
        store.put({"x": b"x"})
