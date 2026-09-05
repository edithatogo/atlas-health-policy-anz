from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pathlib
    from pathlib import Path

    from australian_health_policy_atlas.capture import CaptureReceipt


from dataclasses import replace

import pytest

from australian_health_policy_atlas.crawl import run_crawl, validate_state
from australian_health_policy_atlas.integrity import read_json, sealed
from australian_health_policy_atlas.records import array, record, records
from tests.unit.test_crawl_runtime import fetcher, policy


def state(tmp_path: pathlib.Path) -> dict[str, object]:
    run_crawl(policy(), tmp_path, fetch=fetcher({policy().seed_url: b"x"}))
    return read_json((tmp_path / "state.json").read_bytes())


@pytest.mark.parametrize(
    "mutation",
    ["policy", "empty", "duplicate", "depth", "attempts", "root", "status", "receipt"],
)
def test_resealed_invalid_state_is_rejected(
    tmp_path: pathlib.Path, mutation: str
) -> None:
    value = state(tmp_path)
    target = records(value["targets"])[0]
    mutations = {
        "policy": (
            lambda: record(value["policy"]).update(cutoff="changed"),
            "policy identity mismatch",
        ),
        "empty": (lambda: value.update(targets=[]), "invalid target cardinality"),
        "duplicate": (
            lambda: array(value["targets"]).append(dict(target)),
            "duplicate",
        ),
        "depth": (lambda: target.update(depth=-1), "invalid target budget"),
        "attempts": (lambda: target.update(attempts=-1), "invalid target budget"),
        "root": (lambda: target.update(parent="bogus"), "invalid root target"),
        "status": (
            lambda: target.update(status="made-up"),
            "unknown target disposition",
        ),
        "receipt": (
            lambda: record(target["receipt"]).update(
                requested_url="https://health.test/wrong"
            ),
            "receipt target mismatch",
        ),
    }
    apply_mutation, expected_message = mutations[mutation]
    apply_mutation()
    with pytest.raises(ValueError, match=expected_message):
        validate_state(sealed(value), policy(), tmp_path)


def test_bad_parent_chain(tmp_path: pathlib.Path) -> None:
    value = state(tmp_path)
    target = records(value["targets"])[0]
    target.update(
        url="https://health.test/child", depth=1, parent="not-a-parent", status="queued"
    )
    with pytest.raises(ValueError, match="lineage"):
        validate_state(sealed(value), policy(), tmp_path)


@pytest.mark.parametrize("mutation", ["url", "outside", "hash"])
def test_capture_contract_failures_do_not_become_evidence(
    tmp_path: pathlib.Path, mutation: str
) -> None:
    original = fetcher({policy().seed_url: b"x"})

    def invalid(
        url: str,
        *,
        cas_root: Path,
        max_bytes: int,
        retries: int,
        allowed_hosts: tuple[str, ...],
    ) -> CaptureReceipt:
        receipt = original(
            url,
            cas_root=cas_root,
            max_bytes=max_bytes,
            retries=retries,
            allowed_hosts=allowed_hosts,
        )
        if mutation == "url":
            return replace(receipt, requested_url="https://health.test/wrong")
        if mutation == "outside":
            return replace(receipt, stored_path=str(tmp_path.parent / "escape"))
        return replace(receipt, sha256="a" * 64)

    result = run_crawl(policy(), tmp_path, fetch=invalid)
    assert record(result["counts"])["failed"] == 1
    assert not result["scope_complete"]


def test_cycle_and_duplicate_links_terminate(tmp_path: pathlib.Path) -> None:
    pages = {
        policy().seed_url: (
            b'<a href="/policies">Policies</a><a href="/a.html">Policy</a>'
        ),
        "https://health.test/a.html": b'<a href="/policies">Policies</a>',
    }
    result = run_crawl(policy(), tmp_path, fetch=fetcher(pages))
    assert record(result["counts"])["captured"] == 2
    assert result["scope_complete"]
