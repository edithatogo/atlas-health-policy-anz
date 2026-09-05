import json
from pathlib import Path

from australian_health_policy_atlas.gold import classify_modality, extract_timeframe


def test_adversarial_modality_fixture() -> None:
    for line in (
        Path("quality/benchmarks/adversarial-modality-v1.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ):
        case = json.loads(line)
        assert classify_modality(case["text"]).modality == case["expected"], case["id"]


def test_timeframe_extraction() -> None:
    assert (
        extract_timeframe("Review must occur within 30 minutes.") == "within 30 minutes"
    )
