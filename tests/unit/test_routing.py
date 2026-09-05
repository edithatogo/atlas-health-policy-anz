import pytest

from australian_health_policy_atlas.routing import RouteQualification, choose_route


def test_route_chooses_smallest_qualified() -> None:
    routes = [
        RouteQualification("tiny_local_model", frozenset({"x"}), True),
        RouteQualification("deterministic_rule", frozenset({"x"}), True),
    ]
    assert choose_route("x", routes) == "deterministic_rule"


def test_route_skips_unavailable_or_failed() -> None:
    routes = [
        RouteQualification("deterministic_rule", frozenset({"x"}), False),
        RouteQualification("tiny_local_model", frozenset({"x"}), True, available=False),
        RouteQualification("small_local_model", frozenset({"x"}), True),
    ]
    assert choose_route("x", routes) == "small_local_model"


def test_route_fails_when_nothing_qualified() -> None:
    with pytest.raises(LookupError):
        choose_route("x", [])
