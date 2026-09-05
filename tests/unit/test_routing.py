import pytest

from australian_health_policy_atlas.routing import RouteQualification, choose_route


def test_route_chooses_smallest_qualified() -> None:
    routes = [
        RouteQualification("tiny_local_model", frozenset({"x"}), benchmark_passed=True),
        RouteQualification(
            "deterministic_rule", frozenset({"x"}), benchmark_passed=True
        ),
    ]
    assert choose_route("x", routes) == "deterministic_rule"


def test_route_skips_unavailable_or_failed() -> None:
    routes = [
        RouteQualification(
            "deterministic_rule", frozenset({"x"}), benchmark_passed=False
        ),
        RouteQualification(
            "tiny_local_model", frozenset({"x"}), benchmark_passed=True, available=False
        ),
        RouteQualification(
            "small_local_model", frozenset({"x"}), benchmark_passed=True
        ),
    ]
    assert choose_route("x", routes) == "small_local_model"


def test_route_fails_when_nothing_qualified() -> None:
    with pytest.raises(LookupError):
        choose_route("x", [])
