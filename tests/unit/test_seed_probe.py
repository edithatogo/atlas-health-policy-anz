"""Seed diagnostics retain scoped identities, original bytes and failed attempts."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING
from urllib.error import URLError

import pytest

from australian_health_policy_atlas import seed_probe
from australian_health_policy_atlas.crawl import CrawlPolicy, run_crawl
from australian_health_policy_atlas.hashing import canonical_json_bytes, sha256_json
from australian_health_policy_atlas.integrity import read_json, verify_seal
from australian_health_policy_atlas.operations import load_collection
from australian_health_policy_atlas.records import record, records, strings
from tests.support import ignoring_arguments
from tests.unit.test_crawl_runtime import fetcher

if TYPE_CHECKING:
    from pathlib import Path


def test_plan_covers_exactly_nine_jurisdictions_without_mutating_sources() -> None:
    original = [p.as_dict() for p in load_collection("anz-v1")]
    plan = seed_probe.plan_probe()
    verify_seal(plan)
    policies, parents = seed_probe.probe_policies()
    assert len(policies) == plan["source_count"] == 9
    assert {p.jurisdiction for p in policies} == {
        "ACT",
        "NSW",
        "NT",
        "QLD",
        "SA",
        "TAS",
        "VIC",
        "WA",
        "NZ",
    }
    assert plan["maximum_frontier_attempts"] == 9
    assert plan["maximum_captured_body_bytes"] == 9 * 1024 * 1024
    assert plan["hf_publication_attempted"] is False
    assert plan["capture_executed"] is False
    assert plan["gate_b_passed"] is False
    assert [p.as_dict() for p in load_collection("anz-v1")] == original
    lookup = {p["source_id"]: p for p in original}
    for policy in policies:
        assert policy.max_targets == policy.max_attempts == 1
        assert policy.max_depth == 0
        assert parents[policy.source_id] == sha256_json(
            lookup[policy.source_id.removeprefix("probe-")]
        )
    assert seed_probe.plan_probe() == plan
    assert read_json(canonical_json_bytes(plan)) == plan
    assert all(
        isinstance(row["allowed_hosts"], list) for row in records(plan["policies"])
    )


@pytest.mark.parametrize("variant", ["missing", "duplicate"])
def test_bad_governed_selection_fails_before_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, variant: str
) -> None:
    policies = load_collection("anz-v1")
    altered = (
        [p for p in policies if p.source_id != "authority-nz-moh"]
        if variant == "missing"
        else [*policies, policies[0]]
    )
    monkeypatch.setattr(
        seed_probe, "load_collection", ignoring_arguments(lambda: altered)
    )
    with pytest.raises(ValueError, match="governed"):
        seed_probe.run_probe(tmp_path / "probe")
    assert not (tmp_path / "probe").exists()


def test_success_and_failed_requests_are_both_reconstructable(tmp_path: Path) -> None:
    policies, _parents = seed_probe.probe_policies()
    pages: dict[str, bytes | Exception] = {
        p.seed_url: b"<p>public source bytes</p>" for p in policies
    }
    pages[policies[2].seed_url] = URLError("synthetic access failure")
    seen: list[str] = []
    result = seed_probe.run_probe(tmp_path / "probe", fetch=fetcher(pages, seen))
    verify_seal(result)
    assert result["execution_complete"] is True
    assert len(seen) == len(set(seen)) == 9
    assert result["captured_source_count"] == 8
    assert len(strings(result["selected_source_ids"])) == 9
    observations = records(result["observations"])
    assert len(observations) == 9
    assert all(i["bundle_reconstruction_verified"] is True for i in observations)
    failed = observations[2]
    assert record(record(failed["readiness"])["counts"])["failed"] == 1
    assert record(failed["readiness"])["gate_b_passed"] is False
    assert result["hf_publication_attempted"] is False
    assert result["not_medallion_release"] is True
    assert read_json((tmp_path / "probe/run.json").read_bytes()) == result


def test_default_capture_boundary_exercised_without_network(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    policy = seed_probe.probe_policies()[0][0]

    def isolated_crawl(
        selected: CrawlPolicy, root: Path, *, request_budget: int
    ) -> dict[str, object]:
        return run_crawl(
            selected,
            root,
            request_budget=request_budget,
            fetch=fetcher({selected.seed_url: b"public body"}),
        )

    monkeypatch.setattr(seed_probe, "run_crawl", isolated_crawl)
    result = seed_probe.probe_one(policy, tmp_path / "probe")
    assert result["bundle_reconstruction_verified"] is True
    assert record(record(result["readiness"])["counts"])["captured"] == 1


@pytest.mark.parametrize(
    "field",
    [
        "max_targets",
        "max_attempts",
        "max_depth",
        "max_bytes",
        "max_links_per_page",
        "policy_version",
    ],
)
def test_expanded_probe_limits_are_rejected(tmp_path: Path, field: str) -> None:
    policy = seed_probe.probe_policies()[0][0]
    # Pass modified JSON through the ordinary validator.
    raw = read_json(canonical_json_bytes(policy.as_dict()))
    raw[field] = "unbounded" if field == "policy_version" else 5

    with pytest.raises(ValueError, match="narrow"):
        seed_probe.probe_one(CrawlPolicy.from_record(raw), tmp_path / "probe")
    assert not (tmp_path / "probe").exists()


def test_interruption_retains_full_selection_and_incomplete_journal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    actual = seed_probe.probe_one
    policies = seed_probe.probe_policies()[0]
    port = fetcher({p.seed_url: b"body" for p in policies})
    calls = 0

    def interrupt(
        policy: CrawlPolicy, root: Path, **_options: object
    ) -> dict[str, object]:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise KeyboardInterrupt
        return actual(policy, root, fetch=port)

    monkeypatch.setattr(seed_probe, "probe_one", interrupt)
    with pytest.raises(KeyboardInterrupt):
        seed_probe.run_probe(tmp_path / "probe", fetch=port)
    result = read_json((tmp_path / "probe/run.json").read_bytes())
    verify_seal(result)
    assert result["execution_complete"] is False
    assert result["captured_source_count"] == 1
    assert len(strings(result["selected_source_ids"])) == 9
    assert len(records(result["observations"])) == 1


def test_replay_mismatch_never_reports_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    policy = seed_probe.probe_policies()[0][0]
    monkeypatch.setattr(seed_probe, "restore_bundle", ignoring_arguments(dict))
    with pytest.raises(ValueError, match="reconstruction mismatch"):
        seed_probe.probe_one(
            policy, tmp_path / "probe", fetch=fetcher({policy.seed_url: b"body"})
        )
    assert not (tmp_path / "probe/reference.json").exists()


def test_existing_outputs_and_invalid_policy_are_not_overwritten(
    tmp_path: Path,
) -> None:
    policies, _ = seed_probe.probe_policies()
    output = tmp_path / "probe"
    output.mkdir()
    with pytest.raises(ValueError, match="exists"):
        seed_probe.run_probe(output)
    with pytest.raises(ValueError, match="exists"):
        seed_probe.probe_one(policies[0], output)
    wrong = replace(policies[0], policy_version="not-probe")
    with pytest.raises(ValueError, match="narrow"):
        seed_probe.probe_one(wrong, tmp_path / "invalid")
    assert not (tmp_path / "invalid").exists()


def test_cli_plan_and_isolated_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsysbinary: pytest.CaptureFixture[bytes],
) -> None:
    assert seed_probe.main(["plan", "--output", str(tmp_path / "plan")]) == 0
    assert (
        read_json(capsysbinary.readouterr().out)["kind"] == "governed-seed-probe-plan"
    )
    with pytest.raises(ValueError, match="exists"):
        seed_probe.main(["plan", "--output", str(tmp_path / "plan")])
    actual = seed_probe.run_probe
    policies = seed_probe.probe_policies()[0]
    port = fetcher({p.seed_url: b"body" for p in policies})

    def isolated(output: Path) -> dict[str, object]:
        return actual(output, fetch=port)

    monkeypatch.setattr(seed_probe, "run_probe", isolated)
    assert seed_probe.main(["run", "--output", str(tmp_path / "run")]) == 0
    result = read_json(capsysbinary.readouterr().out)
    assert result["captured_source_count"] == 9
    assert result["gate_b_passed"] is False
