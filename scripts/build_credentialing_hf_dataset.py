"""Build the public credentialing Policy Atlas dataset package."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import TypedDict, cast

ROOT = Path(__file__).resolve().parents[1]
COLLECTION = ROOT / "data" / "source-intake" / "credentialing-socp-anz-20260910"
CATALOGUES = (
    COLLECTION / "schn-medical-surgical-model-catalogue.csv",
    COLLECTION / "schn-paediatric-model-catalogue.csv",
    COLLECTION / "schn-dental-model-catalogue.csv",
)
FORBIDDEN_MARKERS = (
    "patient record",
    "registration number",
    "client_secret",
    "private key",
    "drive.google.com",
)
EXPECTED_CLI_ARGUMENTS = 2
READ_BLOCK_SIZE = 1024 * 1024
README_TEXT = """---
pretty_name: Australian Credentialing and Scope of Clinical Practice Policy Atlas
language:
  - en
license: other
size_categories:
  - n<1K
---

# Australian credentialing and scope-of-clinical-practice Policy Atlas

This public metadata dataset catalogues selected Australian credentialing
authorities and the observed NSW State Scope of Clinical Practice Unit
model-scope library.

It contains no patient, practitioner, credential, referee, committee-case,
tenant or production-system information. Source documents retain their
publisher terms and are not redistributed here.

Catalogue metadata is not a controlled policy instrument. Verify the current
publisher source, authority, effective date, local service capability and
applicable governance before use.
"""


class SourceRow(TypedDict):
    """Public source metadata allowed in the publication package."""

    id: str
    title: str
    publisher: str
    url: str
    authority_class: str


class DatasetReceipt(TypedDict):
    """Deterministic receipt for the built metadata package."""

    schema_version: int
    release: str
    source_rows: int
    model_scope_rows: int
    final_model_rows: int
    under_review_rows: int
    contains_source_binaries: bool
    contains_personal_or_operational_data: bool
    publication_requires_explicit_gate: bool
    evidence_ceiling: str


def read_csv(path: Path) -> list[dict[str, str]]:
    """Read one catalogue and reject incomplete CSV cells.

    Args:
        path: Catalogue path.

    Returns:
        Validated rows containing string keys and values.

    Raises:
        ValueError: If a row contains a missing key or value.

    """
    validated: list[dict[str, str]] = []
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        for row_number, row in enumerate(reader, start=2):
            validated_row: dict[str, str] = {}
            for key, value in row.items():
                if key is None or not isinstance(value, str):
                    message = f"Incomplete CSV row {row_number}: {path}"
                    raise ValueError(message)
                validated_row[key] = value
            validated.append(validated_row)
    return validated


def require_text(value: object, field: str) -> str:
    """Return a required non-empty string.

    Args:
        value: Candidate value.
        field: Field name used in an error message.

    Returns:
        The validated string.

    Raises:
        ValueError: If the value is not a non-empty string.

    """
    if not isinstance(value, str) or not value.strip():
        message = f"Missing required source field: {field}"
        raise ValueError(message)
    return value


def load_sources(path: Path) -> list[SourceRow]:
    """Load and validate the public source metadata boundary.

    Args:
        path: Collection request path.

    Returns:
        Validated public source rows.

    Raises:
        TypeError: If the request or a source has the wrong JSON structure.
        ValueError: If a source field, URL, or identifier is invalid.

    """
    parsed = cast("object", json.loads(path.read_text(encoding="utf-8")))
    if not isinstance(parsed, dict):
        message = "Collection request must be a JSON object"
        raise TypeError(message)
    parsed_mapping = cast("dict[str, object]", parsed)
    raw_sources = parsed_mapping.get("sources")
    if not isinstance(raw_sources, list):
        message = "Collection request must contain a sources array"
        raise TypeError(message)

    sources: list[SourceRow] = []
    for raw_source in cast("list[object]", raw_sources):
        if not isinstance(raw_source, dict):
            message = "Each source must be a JSON object"
            raise TypeError(message)
        source_mapping = cast("dict[str, object]", raw_source)
        source: SourceRow = {
            "id": require_text(source_mapping.get("id"), "id"),
            "title": require_text(source_mapping.get("title"), "title"),
            "publisher": require_text(
                source_mapping.get("publisher"),
                "publisher",
            ),
            "url": require_text(source_mapping.get("url"), "url"),
            "authority_class": require_text(
                source_mapping.get("authority_class"),
                "authority_class",
            ),
        }
        if not source["url"].startswith("https://"):
            message = f"Public source URL must use HTTPS: {source['id']}"
            raise ValueError(message)
        sources.append(source)

    identifiers = [source["id"] for source in sources]
    if len(identifiers) != len(set(identifiers)):
        message = "Public source identifiers must be unique"
        raise ValueError(message)
    return sources


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    """Write deterministic UTF-8 CSV output.

    Args:
        path: Output path.
        rows: Rows to write.
        fields: Ordered field names.

    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=fields,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    """Return the SHA-256 digest for one file.

    Args:
        path: File to hash.

    Returns:
        Lowercase hexadecimal SHA-256 digest.

    """
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(READ_BLOCK_SIZE), b""):
            digest.update(block)
    return digest.hexdigest()


def scan_public_boundary(output: Path) -> None:
    """Fail closed on selected sensitive or internal-publication markers.

    Args:
        output: Built dataset directory.

    Raises:
        ValueError: If a forbidden marker occurs in a generated file.

    """
    for path in output.rglob("*"):
        if not path.is_file():
            continue
        body = path.read_text(encoding="utf-8").lower()
        for marker in FORBIDDEN_MARKERS:
            if marker in body:
                message = (
                    "Public dataset contains forbidden marker "
                    f"{marker!r}: {path}"
                )
                raise ValueError(message)


def write_manifest(output: Path) -> None:
    """Write deterministic fixity records for every generated file.

    Args:
        output: Built dataset directory.

    """
    lines = [
        f"{sha256(path)}  {path.relative_to(output).as_posix()}"
        for path in sorted(output.rglob("*"))
        if path.is_file() and path.name != "MANIFEST.sha256"
    ]
    (output / "MANIFEST.sha256").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def build_dataset(output: Path) -> DatasetReceipt:
    """Build a public metadata-only Hugging Face dataset package.

    Args:
        output: Destination directory. An existing directory is replaced.

    Returns:
        Deterministic dataset receipt.

    """
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    models = [row for catalogue in CATALOGUES for row in read_csv(catalogue)]
    sources = load_sources(COLLECTION / "request.json")

    write_csv(
        output / "data" / "sources.csv",
        [
            {
                "source_id": source["id"],
                "title": source["title"],
                "publisher": source["publisher"],
                "url": source["url"],
                "authority_class": source["authority_class"],
                "observed_date": "2026-09-10",
            }
            for source in sources
        ],
        [
            "source_id",
            "title",
            "publisher",
            "url",
            "authority_class",
            "observed_date",
        ],
    )
    write_csv(
        output / "data" / "model_scopes.csv",
        models,
        [
            "model_id",
            "category",
            "specialty",
            "status",
            "authoritative_listing_url",
            "document_url",
            "verified",
        ],
    )

    final_count = sum(model["status"] == "Final" for model in models)
    receipt: DatasetReceipt = {
        "schema_version": 1,
        "release": "credentialing-socp-anz-20260910",
        "source_rows": len(sources),
        "model_scope_rows": len(models),
        "final_model_rows": final_count,
        "under_review_rows": len(models) - final_count,
        "contains_source_binaries": False,
        "contains_personal_or_operational_data": False,
        "publication_requires_explicit_gate": True,
        "evidence_ceiling": (
            "Public metadata only; not local adoption, source currency after the "
            "observed date, service capability, an individual decision or "
            "operating-effectiveness evidence."
        ),
    }
    (output / "README.md").write_text(README_TEXT, encoding="utf-8")
    (output / "dataset-receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n",
        encoding="utf-8",
    )

    scan_public_boundary(output)
    write_manifest(output)
    return receipt


def parse_output(arguments: list[str]) -> Path:
    """Parse the deliberately small fail-closed command line.

    Args:
        arguments: Command-line arguments excluding the executable name.

    Returns:
        Requested output path.

    Raises:
        ValueError: If the arguments do not contain exactly ``--output PATH``.

    """
    if len(arguments) != EXPECTED_CLI_ARGUMENTS or arguments[0] != "--output":
        message = "Usage: build_credentialing_hf_dataset.py --output PATH"
        raise ValueError(message)
    return Path(arguments[1])


def main() -> int:
    """Build the package and print its receipt.

    Returns:
        Zero when the build completes successfully.

    """
    receipt = build_dataset(parse_output(sys.argv[1:]))
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
