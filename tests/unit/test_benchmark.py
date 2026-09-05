from australian_health_policy_atlas.benchmark import evaluate_classifier


def test_benchmark_counts_abstention_and_error() -> None:
    metrics = evaluate_classifier(
        [
            {"id": "1", "text": "a", "expected": "x"},
            {"id": "2", "text": "b", "expected": None},
        ],
        lambda text: "x" if text == "a" else None,
    )
    assert metrics.accuracy == 1.0
    assert metrics.abstentions == 1
