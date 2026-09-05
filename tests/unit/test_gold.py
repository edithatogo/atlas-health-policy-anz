from pathlib import Path

from australian_health_policy_atlas.gold import classify_modality, extract_timeframe
from australian_health_policy_atlas.records import decode_json, record, string


def test_adversarial_modality_fixture() -> None:
    for line in (
        Path("quality/benchmarks/adversarial-modality-v1.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ):
        case = record(decode_json(line))
        assert classify_modality(string(case["text"])).modality == case["expected"], (
            case["id"]
        )


def test_timeframe_extraction() -> None:
    assert (
        extract_timeframe("Review must occur within 30 minutes.") == "within 30 minutes"
    )
