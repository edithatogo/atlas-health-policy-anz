#!/usr/bin/env python3
"""Benchmark the deterministic modality classifier."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from australian_health_policy_atlas.benchmark import evaluate_classifier, load_jsonl
from australian_health_policy_atlas.gold import classify_modality


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cases", default="quality/benchmarks/adversarial-modality-v1.jsonl"
    )
    parser.add_argument("--output", default="build/benchmarks/modality-v1.json")
    args = parser.parse_args()
    metrics = evaluate_classifier(
        load_jsonl(args.cases), lambda text: classify_modality(text).modality
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(metrics.as_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(metrics.as_dict(), sort_keys=True))
    return 0 if metrics.accuracy == 1.0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
