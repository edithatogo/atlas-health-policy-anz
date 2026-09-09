from __future__ import annotations

import json
from pathlib import Path
from typing import cast

COLLECTION = (
    Path(__file__).parents[2]
    / "data"
    / "source-intake"
    / "credentialing-socp-anz-20260910"
    / "request.json"
)


def _load_collection() -> dict[str, object]:
    return cast("dict[str, object]", json.loads(COLLECTION.read_text(encoding="utf-8")))


def test_credentialing_collection_has_expected_inventory() -> None:
    collection = _load_collection()
    inventory = cast("dict[str, object]", collection["expected_inventory"])
    categories = cast("dict[str, int]", inventory["categories"])

    assert inventory["catalogue_entries"] == 88
    assert inventory["final_models"] == 83
    assert inventory["under_review_after_consultation"] == 5
    assert sum(categories.values()) == 88
    assert categories == {
        "Dental": 12,
        "Medical and surgical": 56,
        "Paediatric": 20,
    }


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
    under_review = cast("list[str]", inventory["under_review_titles"])

    assert under_review == [
        "General Practice",
        "Neurology",
        "Neurosurgery",
        "Orthopaedic Surgery",
        "Urology",
    ]
