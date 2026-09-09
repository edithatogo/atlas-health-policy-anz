"""Offline acquisition plans validate scope and budgets before any side effect."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, cast

import pytest

from australian_health_policy_atlas.capture_plan import compile_plan, main
from australian_health_policy_atlas.integrity import read_json, verify_seal
from australian_health_policy_atlas.operations import load_collection
from australian_health_policy_atlas.operations import main as operate
from australian_health_policy_atlas.records import record, strings
from tests.support import ignoring_arguments

if TYPE_CHECKING:
    from pathlib import Path


def test_exact_collection_plan_is_order_independent_and_budget_bound() -> None:
    policies = load_collection("anz-v1")
    result = compile_plan(policies, "anz-v1", 20)
    verify_seal(result)
    assert result == compile_plan(list(reversed(policies)), "anz-v1", 20)
    assert result["source_count"] == 220
    assert result["maximum_frontier_attempts"] == 4400
    assert len(strings(record(result["matrix"])["source_id"])) == 220
    assert not result["network_used"]
    assert not result["capture_executed"]
    assert not result["gate_b_passed"]
    changed = [
        replace(policies[0], max_targets=policies[0].max_targets + 1),
        *policies[1:],
    ]
    assert (
        compile_plan(changed, "anz-v1", 20)["policies_sha256"]
        != result["policies_sha256"]
    )


@pytest.mark.parametrize("budget", [0, -1, True, 1.5, "20", None, 5121])
def test_invalid_plan_budget_rejected(budget: object) -> None:
    with pytest.raises(ValueError, match="budget"):
        compile_plan(load_collection()[:1], "au-v1", cast("int", budget))


def test_invalid_plan_selection_rejected() -> None:
    policies = load_collection()
    with pytest.raises(ValueError, match="matrix"):
        compile_plan([], "au-v1", 20)
    with pytest.raises(ValueError, match="matrix"):
        compile_plan([policies[0]] * 257, "au-v1", 1)
    with pytest.raises(ValueError, match="duplicate"):
        compile_plan([policies[0]] * 2, "au-v1", 1)
    with pytest.raises(ValueError, match="identity"):
        compile_plan(policies, "", 20)
    with pytest.raises(ValueError, match="max_depth"):
        compile_plan([replace(policies[0], max_depth=-1)], "au-v1", 20)
    with pytest.raises(ValueError, match="aggregate"):
        compile_plan(policies, "au-v1", 5120)


def test_plan_cli_emits_matrix_and_receipt(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    receipt = tmp_path / "plan.json"
    assert main(["--collection", "nz-v1", "--receipt", str(receipt)]) == 0
    result = read_json(receipt.read_bytes())
    assert result["source_count"] == 81
    assert result["matrix"] == read_json(capsys.readouterr().out.encode())
    assert not result["corpus_completeness_claimed"]
    with pytest.raises(ValueError, match="budget"):
        main(["--request-budget", "0", "--receipt", str(tmp_path / "bad.json")])
    assert not (tmp_path / "bad.json").exists()


def test_capture_cli_validates_budget_before_constructing_adapter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    invoked: list[bool] = []
    monkeypatch.setenv("HF_TOKEN", "synthetic-offline-fixture")
    monkeypatch.setattr(
        "australian_health_policy_atlas.operations.HfStore",
        ignoring_arguments(lambda: invoked.append(True)),
    )
    with pytest.raises(SystemExit, match="2"):
        operate([
            "--source-id",
            load_collection()[0].source_id,
            "--request-budget",
            "0",
        ])
    assert not invoked
