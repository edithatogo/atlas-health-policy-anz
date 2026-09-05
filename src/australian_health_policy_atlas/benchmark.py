"""Deterministic benchmark utilities for task-specific route qualification."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable


from dataclasses import dataclass
from pathlib import Path

from .records import decode_json, record


@dataclass(frozen=True, slots=True)
class ClassificationMetrics:
    """Counts, abstentions and accuracy for one labelled classification benchmark."""

    total: int
    correct: int
    accuracy: float
    abstentions: int
    errors: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        """Return this typed record as a serialization-ready dictionary.

        Returns:
            A dictionary containing this record's declared fields.

        """
        return {
            "total": self.total,
            "correct": self.correct,
            "accuracy": self.accuracy,
            "abstentions": self.abstentions,
            "errors": self.errors,
        }


def load_jsonl(path: str | Path) -> list[dict[str, object]]:
    """Decode nonblank JSONL rows into explicitly validated string-keyed records.

    Returns:
        Decoded records in input order, excluding blank lines.

    """
    return [
        record(decode_json(line))
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def evaluate_classifier(
    cases: Iterable[dict[str, object]],
    classifier: Callable[[str], str | None],
) -> ClassificationMetrics:
    """Measure labelled classification results, including abstentions and errors.

    Returns:
        Counts, accuracy, abstentions and failed case identities.

    """
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
