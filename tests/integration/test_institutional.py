import json
from pathlib import Path

from australian_health_policy_atlas.institutional import run_institutional_gap_analysis


def test_institutional_runner_is_local_and_reproducible(tmp_path: Path) -> None:
    local = tmp_path / "local.txt"
    local.write_text(
        "The registered nurse must notify the medical officer within 30 minutes.\n",
        encoding="utf-8",
    )
    baseline = tmp_path / "gold.jsonl"
    baseline.write_text(
        json.dumps({
            "assertion_id": "nsw.1",
            "jurisdiction": "NSW",
            "source_id": "nsw",
            "source_span_id": "s1",
            "actor": "The registered nurse",
            "modality": "should",
            "action": "notify",
            "object": "the medical officer",
            "timeframe": "within 30 minutes",
            "evidence_state": "A0",
            "reason_codes": ["fixture"],
        })
        + "\n",
        encoding="utf-8",
    )
    receipt = run_institutional_gap_analysis(
        local_document=local,
        local_source_id="hospital",
        public_gold_jsonl=baseline,
        output_dir=tmp_path / "out",
    )
    assert receipt["network_used"] is False
    rows = [
        json.loads(line)
        for line in (tmp_path / "out" / "gap-matrix.jsonl").read_text().splitlines()
    ]
    assert rows[0]["relationship"] == "material_difference"
