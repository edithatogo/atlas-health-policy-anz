"""Append-only JSONL execution traces suitable for replay."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .hashing import sha256_json


def append_trace(path: str | Path, *, event_type: str, payload: dict[str, Any], private: bool = False) -> dict[str, Any]:
    event = {
        "schema_version": "1.0",
        "recorded_at": datetime.now(UTC).isoformat(),
        "event_type": event_type,
        "private": private,
        "payload": payload,
    }
    event["event_sha256"] = sha256_json(event)
    trace_path = Path(path)
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    with trace_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    return event
