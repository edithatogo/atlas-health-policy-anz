"""Route bounded tasks to the smallest qualified method."""

from __future__ import annotations

from dataclasses import dataclass


ROUTE_ORDER = (
    "deterministic_rule",
    "lexical_or_structural_model",
    "tiny_local_model",
    "small_local_model",
    "independent_model_triangulation",
    "larger_model_fallback",
)


@dataclass(frozen=True, slots=True)
class RouteQualification:
    route: str
    task_classes: frozenset[str]
    benchmark_passed: bool
    available: bool = True


def choose_route(task_class: str, qualifications: list[RouteQualification]) -> str:
    by_route = {item.route: item for item in qualifications}
    for route in ROUTE_ORDER:
        item = by_route.get(route)
        if item and item.available and item.benchmark_passed and task_class in item.task_classes:
            return route
    raise LookupError(f"no qualified route for task class {task_class}")
