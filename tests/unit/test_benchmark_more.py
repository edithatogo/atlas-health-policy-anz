from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path


from australian_health_policy_atlas.benchmark import evaluate_classifier, load_jsonl
from tests.support import ignoring_arguments


def test_load_jsonl_skips_blank_lines(tmp_path: Path) -> None:
    path = tmp_path / "x.jsonl"
    path.write_text('{"text":"a","expected":"x"}\n\n', encoding="utf-8")
    assert len(load_jsonl(path)) == 1


def test_empty_benchmark_accuracy_zero() -> None:
    result = evaluate_classifier([], ignoring_arguments(lambda: "x"))
    assert result.total == 0
    assert result.accuracy == pytest.approx(0.0)
