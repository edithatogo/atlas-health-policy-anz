from dataclasses import replace

import pytest

from australian_health_policy_atlas.crawl import run_crawl, validate_state
from australian_health_policy_atlas.integrity import read_json, sealed
from tests.unit.test_crawl_runtime import fetcher, policy


def state(tmp_path):
    run_crawl(policy(), tmp_path, fetch=fetcher({policy().seed_url: b"x"}))
    return read_json((tmp_path / "state.json").read_bytes())


@pytest.mark.parametrize(
    "mutation",
    ["policy", "empty", "duplicate", "depth", "attempts", "root", "status", "receipt"],
)
def test_resealed_invalid_state_is_rejected(tmp_path, mutation):
    value = state(tmp_path)
    target = value["targets"][0]
    if mutation == "policy":
        value["policy"]["cutoff"] = "changed"
    if mutation == "empty":
        value["targets"] = []
    if mutation == "duplicate":
        value["targets"].append(dict(target))
    if mutation == "depth":
        target["depth"] = -1
    if mutation == "attempts":
        target["attempts"] = -1
    if mutation == "root":
        target["parent"] = "bogus"
    if mutation == "status":
        target["status"] = "made-up"
    if mutation == "receipt":
        target["receipt"]["requested_url"] = "https://health.test/wrong"
    with pytest.raises(ValueError):
        validate_state(sealed(value), policy(), tmp_path)


def test_bad_parent_chain(tmp_path):
    value = state(tmp_path)
    target = value["targets"][0]
    target.update(
        url="https://health.test/child", depth=1, parent="not-a-parent", status="queued"
    )
    with pytest.raises(ValueError, match="lineage"):
        validate_state(sealed(value), policy(), tmp_path)


@pytest.mark.parametrize("mutation", ["url", "outside", "hash"])
def test_capture_contract_failures_do_not_become_evidence(tmp_path, mutation):
    original = fetcher({policy().seed_url: b"x"})

    def invalid(url, **kwargs):
        receipt = original(url, **kwargs)
        if mutation == "url":
            return replace(receipt, requested_url="https://health.test/wrong")
        if mutation == "outside":
            return replace(receipt, stored_path=str(tmp_path.parent / "escape"))
        return replace(receipt, sha256="a" * 64)

    result = run_crawl(policy(), tmp_path, fetch=invalid)
    assert result["counts"]["failed"] == 1
    assert not result["scope_complete"]


def test_cycle_and_duplicate_links_terminate(tmp_path):
    pages = {
        policy().seed_url: b'<a href="/policies">Policies</a><a href="/a.html">Policy</a>',
        "https://health.test/a.html": b'<a href="/policies">Policies</a>',
    }
    result = run_crawl(policy(), tmp_path, fetch=fetcher(pages))
    assert result["counts"]["captured"] == 2
    assert result["scope_complete"]
