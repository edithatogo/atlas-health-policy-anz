"""Different collections cannot borrow the AU v1 completeness denominator."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pytest

    from australian_health_policy_atlas.crawl import CrawlPolicy


import pathlib
from pathlib import Path

from scripts import assess_bronze as module

from australian_health_policy_atlas.integrity import sealed, verify_seal
from australian_health_policy_atlas.records import decode_json, record, string
from tests.support import ignoring_arguments

ROOT = Path(__file__).resolve().parents[2]


def test_distinct_scope_identities() -> None:
    au, au_hash, au_kind = module.assessment_scope("au-v1")
    nz, nz_hash, nz_kind = module.assessment_scope("nz-v1")
    anz, anz_hash, anz_kind = module.assessment_scope("anz-v1")
    assert (len(au), len(nz), len(anz)) == (28, 81, 220)
    assert len({au_hash, nz_hash, anz_hash}) == 3
    assert au_kind.startswith("frozen")
    assert nz_kind == anz_kind


def test_missing_credential_is_explicit(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("HF_TOKEN", raising=False)
    assert module.main(["--collection", "nz-v1"]) == 2
    assert record(decode_json(capsys.readouterr().out))["collection"] == "nz-v1"


def test_assessment_binds_selected_scope_without_network(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("HF_TOKEN", "fixture-only-no-credential")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        module.subprocess, "check_output", ignoring_arguments(lambda: "1" * 40)
    )
    monkeypatch.setattr(module, "HfStore", ignoring_arguments(object))

    def assess(
        _hub: object,
        policies: list[CrawlPolicy],
        *,
        census_sha256: str,
        code_revision: str,
    ) -> dict[str, object]:
        assert len(policies) == 81
        assert code_revision == "1" * 40
        return sealed({
            "expected_sources": len(policies),
            "census_sha256": census_sha256,
            "gate_b_passed": False,
        })

    monkeypatch.setattr(module, "qualify_remote_bronze", assess)
    assert module.main(["--collection", "nz-v1"]) == 0
    row = record(decode_json(capsys.readouterr().out))
    verify_seal(row)
    assert row["collection"] == "nz-v1"
    assert row["gate_b_passed"] is False
    assert "not-document-census" in string(row["scope_identity_kind"])
    assert (
        record(
            decode_json(
                Path("build/receipts/bronze-assessment.json").read_text(
                    encoding="utf-8"
                )
            )
        )
        == row
    )
