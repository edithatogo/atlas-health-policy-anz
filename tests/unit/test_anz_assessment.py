"""Different collections cannot borrow the AU v1 completeness denominator."""

import importlib.util
import json
from pathlib import Path

from australian_health_policy_atlas.integrity import sealed, verify_seal

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "assess_anz", ROOT / "scripts/assess_bronze.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_distinct_scope_identities():
    au, au_hash, au_kind = module.assessment_scope("au-v1")
    nz, nz_hash, nz_kind = module.assessment_scope("nz-v1")
    anz, anz_hash, anz_kind = module.assessment_scope("anz-v1")
    assert (len(au), len(nz), len(anz)) == (28, 81, 220)
    assert len({au_hash, nz_hash, anz_hash}) == 3
    assert au_kind.startswith("frozen")
    assert nz_kind == anz_kind


def test_missing_credential_is_explicit(monkeypatch, capsys):
    monkeypatch.delenv("HF_TOKEN", raising=False)
    assert module.main(["--collection", "nz-v1"]) == 2
    assert json.loads(capsys.readouterr().out)["collection"] == "nz-v1"


def test_assessment_binds_selected_scope_without_network(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("HF_TOKEN", "fixture-only-no-credential")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(module.subprocess, "check_output", lambda *a, **k: "1" * 40)
    monkeypatch.setattr(module, "HfStore", lambda *a: object())

    def assess(hub, policies, *, census_sha256, code_revision):
        assert len(policies) == 81
        assert code_revision == "1" * 40
        return sealed({
            "expected_sources": len(policies),
            "census_sha256": census_sha256,
            "gate_b_passed": False,
        })

    monkeypatch.setattr(module, "qualify_remote_bronze", assess)
    assert module.main(["--collection", "nz-v1"]) == 0
    row = json.loads(capsys.readouterr().out)
    verify_seal(row)
    assert row["collection"] == "nz-v1"
    assert row["gate_b_passed"] is False
    assert "not-document-census" in row["scope_identity_kind"]
    assert json.loads(Path("build/receipts/bronze-assessment.json").read_text()) == row
