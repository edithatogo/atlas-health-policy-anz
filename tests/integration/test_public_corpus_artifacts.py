from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_source_census_v1_is_closed_and_hash_bound() -> None:
    registry_path = ROOT / "data/sources/source-surfaces-v1.json"
    completion = json.loads((ROOT / "evidence/public-corpus/source-census-v1/completion.json").read_text())
    registry = json.loads(registry_path.read_text())
    jurisdictions = {item["jurisdiction"] for item in registry["sources"]}
    assert {"QLD", "NSW", "VIC", "SA", "WA", "TAS", "ACT", "NT", "Cth"} <= jurisdictions
    assert completion["status"] == "qualified"
    assert completion["source_surface_count"] == len(registry["sources"])
    assert completion["registry_sha256"] == hashlib.sha256(registry_path.read_bytes()).hexdigest()


def test_bronze_readiness_fails_closed_without_original_bytes() -> None:
    readiness = json.loads((ROOT / "evidence/public-corpus/bronze-v1/readiness.json").read_text())
    assert readiness["status"] == "executing"
    assert readiness["original_payloads_captured"] == 0
    assert readiness["gate_b_passed"] is False
    assert readiness["blockers"]


def test_shadow_vertical_slice_cannot_be_misrepresented_as_release() -> None:
    shadow = ROOT / "quality/shadow/clinical-governance-v0"
    receipt = json.loads((shadow / "receipt.json").read_text())
    preview = json.loads((shadow / "platinum-preview.json").read_text())
    assert receipt["not_a_medallion_release"] is True
    assert preview["not_a_medallion_release"] is True
    assert preview["production_promotion_allowed"] is False
    rows = {row["jurisdiction"]: row for row in preview["rows"]}
    assert rows["QLD"]["comparability"] == "scope-limited"
    assert rows["NT"]["comparability"] == "scope-limited"
    assert rows["TAS"]["comparability"] == "secondary-framework-reference"
