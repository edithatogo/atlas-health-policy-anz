from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


from australian_health_policy_atlas.records import decode_json, record
from australian_health_policy_atlas.trace import append_trace


def test_trace_is_append_only_jsonl(tmp_path: Path) -> None:
    path = tmp_path / "trace.jsonl"
    first = append_trace(path, event_type="test", payload={"x": 1})
    append_trace(path, event_type="test", payload={"x": 2})
    rows = [
        record(decode_json(line))
        for line in path.read_text(encoding="utf-8").splitlines()
    ]
    assert len(rows) == 2
    assert rows[0]["event_sha256"] == first["event_sha256"]
