from __future__ import annotations

import hashlib
from pathlib import Path

from australian_health_policy_atlas.records import array, decode_json, record, records

ROOT = Path(__file__).resolve().parents[2]


def test_source_census_v1_is_closed_and_hash_bound() -> None:
    registry_path = ROOT / "data/sources/source-surfaces-v1.json"
    completion = record(
        decode_json(
            (
                ROOT / "evidence/public-corpus/source-census-v1/completion.json"
            ).read_text()
        )
    )
    registry = record(decode_json(registry_path.read_text()))
    jurisdictions = {item["jurisdiction"] for item in records(registry["sources"])}
    assert {"QLD", "NSW", "VIC", "SA", "WA", "TAS", "ACT", "NT", "Cth"} <= jurisdictions
    assert completion["status"] == "qualified"
    assert completion["source_surface_count"] == len(array(registry["sources"]))
    assert (
        completion["registry_sha256"]
        == hashlib.sha256(registry_path.read_bytes()).hexdigest()
    )


def test_bronze_readiness_fails_closed_without_original_bytes() -> None:
    readiness = record(
        decode_json(
            (ROOT / "evidence/public-corpus/bronze-v1/readiness.json").read_text()
        )
    )
    assert readiness["status"] == "executing"
    assert readiness["original_payloads_captured"] == 0
    assert readiness["gate_b_passed"] is False
    assert readiness["blockers"]


def test_shadow_vertical_slice_cannot_be_misrepresented_as_release() -> None:
    shadow = ROOT / "quality/shadow/clinical-governance-v0"
    receipt = record(decode_json((shadow / "receipt.json").read_text()))
    preview = record(decode_json((shadow / "platinum-preview.json").read_text()))
    assert receipt["not_a_medallion_release"] is True
    assert preview["not_a_medallion_release"] is True
    assert preview["production_promotion_allowed"] is False
    rows = {row["jurisdiction"]: row for row in records(preview["rows"])}
    assert rows["QLD"]["comparability"] == "scope-limited"
    assert rows["NT"]["comparability"] == "scope-limited"
    assert rows["TAS"]["comparability"] == "secondary-framework-reference"
