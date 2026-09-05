"""Bronze content-addressed ingestion and manifest generation."""

from __future__ import annotations

import json
import mimetypes
import shutil
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from .hashing import sha256_file, sha256_json


@dataclass(frozen=True, slots=True)
class BronzeObject:
    object_id: str
    source_id: str
    source_uri: str
    sha256: str
    size_bytes: int
    media_type: str
    observed_at: str
    stored_path: str


def ingest_local_file(
    source_path: str | Path,
    *,
    source_id: str,
    source_uri: str,
    cas_root: str | Path,
    observed_at: str | None = None,
) -> BronzeObject:
    source = Path(source_path)
    digest = sha256_file(source)
    target = Path(cas_root) / "sha256" / digest[:2] / digest
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        shutil.copyfile(source, target)
    stored_digest = sha256_file(target)
    if stored_digest != digest:
        raise OSError("CAS verification failed after copy")
    media_type = mimetypes.guess_type(source.name)[0] or "application/octet-stream"
    return BronzeObject(
        object_id=f"sha256:{digest}",
        source_id=source_id,
        source_uri=source_uri,
        sha256=digest,
        size_bytes=source.stat().st_size,
        media_type=media_type,
        observed_at=observed_at or datetime.now(UTC).isoformat(),
        stored_path=str(target),
    )


def write_manifest(
    objects: Iterable[BronzeObject], path: str | Path, *, release_id: str
) -> dict[str, object]:
    records = [asdict(item) for item in objects]
    payload: dict[str, object] = {
        "schema_version": "1.0",
        "release_id": release_id,
        "layer": "bronze",
        "record_count": len(records),
        "objects": records,
    }
    payload["manifest_sha256"] = sha256_json(payload)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return payload
