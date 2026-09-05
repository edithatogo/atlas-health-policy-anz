from __future__ import annotations

import math
import pathlib

import pytest

from australian_health_policy_atlas.domain import MedallionLayer
from australian_health_policy_atlas.hashing import canonical_json_bytes
from australian_health_policy_atlas.integrity import (
    atomic_json,
    read_json,
    safe_path,
    sealed,
    verify_seal,
)
from australian_health_policy_atlas.state_machine import promotion_gate


def test_atomic_sealed_roundtrip(tmp_path: pathlib.Path) -> None:
    path = tmp_path / "sub" / "state.json"
    value = sealed({"generation": 1})
    atomic_json(path, value)
    assert read_json(path.read_bytes()) == value
    verify_seal(value)
    value["generation"] = 2
    with pytest.raises(ValueError, match="self-hash"):
        verify_seal(value)


@pytest.mark.parametrize(
    "data", [b'{"a":1,"a":2}', b"[]", b'{"x":NaN}', b'{"x":Infinity}']
)
def test_strict_json(data) -> None:
    with pytest.raises(ValueError):
        read_json(data)


@pytest.mark.parametrize(
    "path", ["../x", "/x", "a/../../x", "C:/x", "a\\x", "", "a//x"]
)
def test_unsafe_paths(tmp_path: pathlib.Path, path) -> None:
    with pytest.raises(ValueError):
        safe_path(tmp_path, path)


def test_symlink_path(tmp_path: pathlib.Path) -> None:
    (tmp_path / "link").symlink_to(tmp_path / "target")
    with pytest.raises(ValueError):
        safe_path(tmp_path, "link/file")


def test_nonfinite_canonical_json() -> None:
    with pytest.raises(ValueError):
        canonical_json_bytes({"invalid": math.nan})


@pytest.mark.parametrize(
    "acceptance",
    [{}, {"fixity": "false"}, {"fixity": 1}, {"fixity": []}, {"fixity": None}],
)
def test_empty_and_non_boolean_acceptance_blocked(acceptance) -> None:
    assert not promotion_gate(
        MedallionLayer.CENSUS, closed_layers=set(), acceptance_results=acceptance
    ).permitted
