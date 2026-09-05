"""Deterministic benchmark utilities for task-specific route qualification."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ClassificationMetrics:
    total: int
    correct: int
    accuracy: float
    abstentions: int
    errors: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def load_jsonl(path: str | Path) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def evaluate_classifier(
    cases: Iterable[dict[str, object]],
    classifier: Callable[[str], str | None],
) -> ClassificationMetrics:
    total = correct = abstentions = 0
    errors: list[str] = []
    for case in cases:
        total += 1
        predicted = classifier(str(case["text"]))
        expected = case.get("expected")
        if predicted is None:
            abstentions += 1
        if predicted == expected:
            correct += 1
        else:
            errors.append(str(case.get("id", total)))
    return ClassificationMetrics(
        total=total,
        correct=correct,
        accuracy=(correct / total if total else 0.0),
        abstentions=abstentions,
        errors=tuple(errors),
    )
