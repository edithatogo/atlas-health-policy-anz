"""Load and validate the governed jurisdiction source registry."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

JURISDICTIONS = frozenset({
    "Cth",
    "ACT",
    "NSW",
    "NT",
    "QLD",
    "SA",
    "TAS",
    "VIC",
    "WA",
    "NZ",
    "ANZ",
})


def load_registry(path: str | Path | None = None) -> dict[str, Any]:
    if path is None:
        from importlib.resources import files

        resource = files("australian_health_policy_atlas").joinpath(
            "_data/jurisdictions-v1.json"
        )
        if resource.is_file():
            text = resource.read_text(encoding="utf-8")
        else:
            text = (
                Path(__file__).resolve().parents[2]
                / "data/sources/jurisdictions-v1.json"
            ).read_text(encoding="utf-8")
    else:
        text = Path(path).read_text(encoding="utf-8")
    value = json.loads(text)
    validate_registry(value)
    return value


def validate_registry(value: dict[str, Any]) -> None:
    if value.get("schema_version") != "1.0":
        raise ValueError("unsupported source registry schema")
    seen: set[str] = set()
    for source in value.get("sources", []):
        source_id = source["source_id"]
        if source_id in seen:
            raise ValueError(f"duplicate source_id: {source_id}")
        seen.add(source_id)
        if source["jurisdiction"] not in JURISDICTIONS:
            raise ValueError(f"unknown jurisdiction: {source['jurisdiction']}")
        parsed = urlparse(source["url"])
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError(f"source URL must be https: {source_id}")
        if source.get("authority") != "official":
            raise ValueError(f"registry source must be official: {source_id}")
