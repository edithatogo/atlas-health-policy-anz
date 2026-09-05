from __future__ import annotations

import pathlib
from dataclasses import replace
from urllib.error import HTTPError, URLError

import pytest

from australian_health_policy_atlas.capture import CaptureReceipt
from australian_health_policy_atlas.crawl import CrawlPolicy, run_crawl
from australian_health_policy_atlas.hashing import sha256_bytes
from australian_health_policy_atlas.integrity import atomic_json, read_json


def policy(**changes):
    base = CrawlPolicy(
        "qld-test",
        "QLD",
        "https://health.test/policies",
        ("health.test",),
        "2026-09-03",
    )
    return replace(base, **changes)


def fetcher(pages, seen=None):
    def fetch(url, *, cas_root, **_kwargs):
        if seen is not None:
            seen.append(url)
        data = pages[url]
        if isinstance(data, Exception):
            raise data
        digest = sha256_bytes(data)
        file = cas_root / "sha256" / digest[:2] / digest
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(data)
        return CaptureReceipt(
            url,
            url,
            200,
            "2026-09-05T00:00:00+00:00",
            digest,
            len(data),
            "application/pdf" if url.endswith(".pdf") else "text/html",
            None,
            None,
            str(file),
        )

    return fetch


def test_crawl_resume_without_recapture(tmp_path: pathlib.Path) -> None:
    pages = {
        "https://health.test/policies": b'<a href="/policy.pdf">Policy</a>',
        "https://health.test/policy.pdf": b"%PDF-original-fixture",
    }
    seen = []
    first = run_crawl(policy(), tmp_path, request_budget=1, fetch=fetcher(pages, seen))
    assert first["counts"]["queued"] == 1
    assert not first["scope_complete"]
    second = run_crawl(policy(), tmp_path, request_budget=1, fetch=fetcher(pages, seen))
    assert second["scope_complete"]
    assert not second["gate_b_passed"]
    assert second["counts"]["captured"] == 2
    run_crawl(policy(), tmp_path, fetch=fetcher(pages, seen))
    assert len(seen) == 2


@pytest.mark.parametrize(
    "changes,reason",
    [
        ({"max_depth": 0}, "depth_limit"),
        ({"max_targets": 1}, "target_limit"),
        ({"max_links_per_page": 1}, "link_limit"),
    ],
)
def test_limits_are_not_exhaustive_coverage(
    tmp_path: pathlib.Path, changes, reason
) -> None:
    pages = {
        "https://health.test/policies": b'<a href="/a.pdf">A</a><a href="/b.pdf">B</a>',
        "https://health.test/a.pdf": b"a",
        "https://health.test/b.pdf": b"b",
    }
    result = run_crawl(policy(**changes), tmp_path, fetch=fetcher(pages))
    assert result["frontier_exhausted"]
    assert not result["scope_complete"]
    assert reason in {
        b["reason"]
        for b in read_json((tmp_path / "state.json").read_bytes())["boundaries"]
    }


def test_external_link_is_accounted(tmp_path: pathlib.Path) -> None:
    result = run_crawl(
        policy(),
        tmp_path,
        fetch=fetcher({
            "https://health.test/policies": b'<a href="https://other.test/policy.pdf">Policy</a>'
        }),
    )
    assert not result["scope_complete"]


@pytest.mark.parametrize(
    "status,expected",
    [
        (404, "unavailable"),
        (410, "unavailable"),
        (403, "restricted"),
        (401, "restricted"),
        (400, "failed"),
        (429, "retryable"),
        (503, "retryable"),
    ],
)
def test_http_dispositions(tmp_path: pathlib.Path, status, expected) -> None:
    result = run_crawl(
        policy(),
        tmp_path,
        fetch=fetcher({
            "https://health.test/policies": HTTPError(
                "https://health.test/policies", status, "test", {}, None
            )
        }),
    )
    assert result["counts"][expected] == 1
    assert not result["scope_complete"]


def test_retries_are_bounded(tmp_path: pathlib.Path) -> None:
    fetch = fetcher({"https://health.test/policies": URLError("network unavailable")})
    for _ in range(5):
        result = run_crawl(policy(max_attempts=2), tmp_path, fetch=fetch)
    assert result["counts"]["failed"] == 1
    state = read_json((tmp_path / "state.json").read_bytes())
    assert state["targets"][0]["attempts"] == 2


@pytest.mark.parametrize(
    "error,kind",
    [
        (ValueError("max_bytes exceeded"), "oversized"),
        (ValueError("bad capture"), "failed"),
        (OSError("temporary"), "retryable"),
    ],
)
def test_capture_errors(tmp_path: pathlib.Path, error, kind) -> None:
    result = run_crawl(
        policy(), tmp_path, fetch=fetcher({"https://health.test/policies": error})
    )
    assert result["counts"][kind] == 1


def test_scope_drift_and_tamper_rejected(tmp_path: pathlib.Path) -> None:
    fetch = fetcher({"https://health.test/policies": b"hello"})
    run_crawl(policy(), tmp_path, fetch=fetch)
    with pytest.raises(ValueError, match="policy changed"):
        run_crawl(policy(max_depth=3), tmp_path, fetch=fetch)
    state = read_json((tmp_path / "state.json").read_bytes())
    (tmp_path / state["targets"][0]["receipt"]["object_path"]).write_bytes(b"tampered")
    with pytest.raises(ValueError, match="fixity"):
        run_crawl(policy(), tmp_path, fetch=fetch)


def test_resume_selfhash_fails(tmp_path: pathlib.Path) -> None:
    run_crawl(policy(), tmp_path, fetch=fetcher({"https://health.test/policies": b"x"}))
    state = read_json((tmp_path / "state.json").read_bytes())
    state["generation"] += 1
    atomic_json(tmp_path / "state.json", state)
    with pytest.raises(ValueError, match="self-hash"):
        run_crawl(policy(), tmp_path)


@pytest.mark.parametrize(
    "changes",
    [
        {"max_targets": 0},
        {"max_attempts": True},
        {"max_depth": -1},
        {"source_id": "../x"},
        {"jurisdiction": "XX"},
        {"cutoff": ""},
        {"allowed_hosts": ("wrong.test",)},
    ],
)
def test_invalid_policy(changes) -> None:
    with pytest.raises(ValueError):
        policy(**changes).validate()


def test_request_budget(tmp_path: pathlib.Path) -> None:
    with pytest.raises(ValueError):
        run_crawl(policy(), tmp_path, request_budget=0)
