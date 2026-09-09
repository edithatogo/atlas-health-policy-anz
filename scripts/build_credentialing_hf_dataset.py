#!/usr/bin/env python3
"""Build and optionally publish the public credentialing Policy Atlas dataset."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import json
import shutil
from pathlib import Path
from typing import Any, cast

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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return cast("list[dict[str, str]]", list(csv.DictReader(stream)))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_dataset(output: Path) -> dict[str, Any]:
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    request = cast(
        "dict[str, Any]",
        json.loads((COLLECTION / "request.json").read_text(encoding="utf-8")),
    )
    models = [row for catalogue in CATALOGUES for row in read_csv(catalogue)]
    sources = cast("list[dict[str, str]]", request["sources"])

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
    under_review_count = len(models) - final_count
    readme = """---
pretty_name: Australian Credentialing and Scope of Clinical Practice Policy Atlas
language:
  - en
license: other
size_categories:
  - n<1K
---

# Australian credentialing and scope-of-clinical-practice Policy Atlas

This public metadata dataset catalogues selected Australian credentialing authorities and the observed NSW State Scope of Clinical Practice Unit model-scope library.

It contains no patient, practitioner, credential, referee, committee-case, tenant or production-system information. Source documents retain their publisher terms and are not redistributed here.

Catalogue metadata is not a controlled policy instrument. Verify the current publisher source, legal or policy authority, effective date, local service capability and applicable governance before use.
"""
    (output / "README.md").write_text(readme, encoding="utf-8")
    receipt = {
        "schema_version": 1,
        "release": "credentialing-socp-anz-20260910",
        "source_rows": len(sources),
        "model_scope_rows": len(models),
        "final_model_rows": final_count,
        "under_review_rows": under_review_count,
        "contains_source_binaries": False,
        "contains_personal_or_operational_data": False,
        "publication_requires_explicit_flag": True,
        "evidence_ceiling": (
            "Public metadata only; not local adoption, source currency after the observed date, "
            "service capability, an individual decision or operating-effectiveness evidence."
        ),
    }
    (output / "dataset-receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n",
        encoding="utf-8",
    )

    for path in output.rglob("*"):
        if not path.is_file():
            continue
        body = path.read_text(encoding="utf-8").lower()
        for marker in FORBIDDEN_MARKERS:
            if marker in body:
                msg = f"Public dataset contains forbidden marker {marker!r}: {path}"
                raise ValueError(msg)

    manifest_lines = [
        f"{sha256(path)}  {path.relative_to(output).as_posix()}"
        for path in sorted(output.rglob("*"))
        if path.is_file() and path.name != "MANIFEST.sha256"
    ]
    (output / "MANIFEST.sha256").write_text(
        "\n".join(manifest_lines) + "\n",
        encoding="utf-8",
    )
    return receipt


def publish_dataset(output: Path, dataset_id: str, token: str | None) -> str:
    if not token:
        msg = "HF_TOKEN is required when --publish is set"
        raise ValueError(msg)
    module = importlib.import_module("huggingface_hub")
    api_type = getattr(module, "HfApi")
    api = api_type(token=token)
    api.create_repo(repo_id=dataset_id, repo_type="dataset", exist_ok=True)
    result = api.upload_folder(
        repo_id=dataset_id,
        repo_type="dataset",
        folder_path=str(output),
        commit_message="Publish credentialing Policy Atlas public metadata",
    )
    return str(result)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--dataset-id")
    parser.add_argument("--token")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    receipt = build_dataset(args.output)
    print(json.dumps(receipt, indent=2))
    if args.publish:
        if not args.dataset_id:
            msg = "--dataset-id is required when --publish is set"
            raise ValueError(msg)
        print(publish_dataset(args.output, args.dataset_id, args.token))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
