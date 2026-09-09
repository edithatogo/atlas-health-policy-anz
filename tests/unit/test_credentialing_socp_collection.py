from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import cast

COLLECTION_DIR = (
    Path(__file__).parents[2]
    / "data"
    / "source-intake"
    / "credentialing-socp-anz-20260910"
)
COLLECTION = COLLECTION_DIR / "request.json"
CATALOGUES = (
    COLLECTION_DIR / "schn-medical-surgical-model-catalogue.csv",
    COLLECTION_DIR / "schn-paediatric-model-catalogue.csv",
    COLLECTION_DIR / "schn-dental-model-catalogue.csv",
)


def _load_collection() -> dict[str, object]:
    return cast("dict[str, object]", json.loads(COLLECTION.read_text(encoding="utf-8")))


def _load_models() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in CATALOGUES:
        with path.open(encoding="utf-8", newline="") as stream:
            rows.extend(cast("list[dict[str, str]]", list(csv.DictReader(stream))))
    return rows


def test_credentialing_collection_has_expected_inventory() -> None:
    collection = _load_collection()
    inventory = cast("dict[str, object]", collection["expected_inventory"])
    expected_categories = cast("dict[str, int]", inventory["categories"])
    models = _load_models()
    categories = Counter(model["category"] for model in models)
    statuses = Counter(model["status"] for model in models)

    assert len(models) == inventory["catalogue_entries"] == 88
    assert statuses["Final"] == inventory["final_models"] == 83
    assert (
        statuses["Under review after consultation"]
        == inventory["under_review_after_consultation"]
        == 5
    )
    assert categories == expected_categories == {
        "Dental": 12,
        "Medical and surgical": 56,
        "Paediatric": 20,
    }
    model_ids = [model["model_id"] for model in models]
    assert len(model_ids) == len(set(model_ids))


def test_credentialing_collection_is_metadata_only_and_fail_closed() -> None:
    collection = _load_collection()
    sources = cast("list[dict[str, object]]", collection["sources"])
    source_ids = [cast("str", source["id"]) for source in sources]

    assert collection["publication_class"] == "public-source-metadata-only"
    assert collection["evaluation_material_allowed"] is False
    assert collection["medallion_promotion"] is False
    assert collection["python_target"] == "3.14"
    assert len(source_ids) == len(set(source_ids))
    assert all(cast("str", source["url"]).startswith("https://") for source in sources)
    assert "schn-model-scopes-paediatric" in source_ids
    assert "schn-model-scopes-medical-surgical" in source_ids
    assert "schn-model-scopes-dental" in source_ids
    assert "qld-health-hsd-034" in source_ids
    assert "acsqhc-credentialing-guidance-2026" in source_ids


def test_under_review_models_are_explicit() -> None:
    collection = _load_collection()
    inventory = cast("dict[str, object]", collection["expected_inventory"])
    expected = cast("list[str]", inventory["under_review_titles"])
    observed = [
        model["specialty"]
        for model in _load_models()
        if model["status"] == "Under review after consultation"
    ]

    assert observed == expected == [
        "General Practice",
        "Neurology",
        "Neurosurgery",
        "Orthopaedic Surgery",
        "Urology",
    ]


def test_model_rows_preserve_source_and_evidence_ceiling() -> None:
    for model in _load_models():
        assert model["authoritative_listing_url"].startswith("https://")
        assert model["verified"] == "2026-09-10"
        assert model["status"] in {"Final", "Under review after consultation"}
        if model["document_url"]:
            assert model["document_url"].startswith("https://")
