"""Load and validate the governed jurisdiction source registry."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path
from typing import TypedDict
from urllib.parse import urlparse

from .records import decode_json, record, records, string, strings

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


class RegistrySource(TypedDict):
    """Validated official acquisition surface, not a captured policy."""

    source_id: str
    jurisdiction: str
    authority: str
    publisher: str
    surface_type: str
    url: str
    document_classes: list[str]


class SourceRegistry(TypedDict):
    """Versioned acquisition surfaces and their observation context."""

    schema_version: str
    observation_date: str
    scope_note: str
    sources: list[RegistrySource]


def _registry_text(path: str | Path | None) -> str:
    if path is not None:
        return Path(path).read_text(encoding="utf-8")
    resource = files("australian_health_policy_atlas").joinpath(
        "_data/jurisdictions-v1.json"
    )
    if resource.is_file():
        return resource.read_text(encoding="utf-8")
    return (
        Path(__file__).resolve().parents[2] / "data/sources/jurisdictions-v1.json"
    ).read_text(encoding="utf-8")


def load_registry(path: str | Path | None = None) -> SourceRegistry:
    """Return registry fields validated before conversion to their typed shape.

    Returns:
        The validated registry with all source identities preserved.

    """
    value = record(decode_json(_registry_text(path)))
    validate_registry(value)
    sources: list[RegistrySource] = [
        RegistrySource(
            source_id=string(row["source_id"]),
            jurisdiction=string(row["jurisdiction"]),
            authority=string(row["authority"]),
            publisher=string(row["publisher"]),
            surface_type=string(row["surface_type"]),
            url=string(row["url"]),
            document_classes=strings(row["document_classes"]),
        )
        for row in records(value.get("sources", []))
    ]
    return SourceRegistry(
        schema_version=string(value["schema_version"]),
        observation_date=string(value.get("observation_date", "")),
        scope_note=string(value.get("scope_note", "")),
        sources=sources,
    )


def validate_registry(value: object) -> None:
    """Reject invalid schema, repeated identities, and unofficial HTTP surfaces.

    Raises:
        ValueError: A source violates the versioned registry contract.

    """
    registry = record(value)
    if registry.get("schema_version") != "1.0":
        message = "unsupported source registry schema"
        raise ValueError(message)
    seen: set[str] = set()
    for source in records(registry.get("sources", [])):
        source_id = string(source["source_id"])
        if source_id in seen:
            message = f"duplicate source_id: {source_id}"
            raise ValueError(message)
        seen.add(source_id)
        if source["jurisdiction"] not in JURISDICTIONS:
            message = f"unknown jurisdiction: {source['jurisdiction']}"
            raise ValueError(message)
        parsed = urlparse(string(source["url"]))
        if parsed.scheme != "https" or not parsed.netloc:
            message = f"source URL must be https: {source_id}"
            raise ValueError(message)
        if source.get("authority") != "official":
            message = f"registry source must be official: {source_id}"
            raise ValueError(message)
