"""Typed factories for isolated test doubles, not alternative production adapters."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


def ignoring_arguments[T](factory: Callable[[], T]) -> Callable[..., T]:
    """Evaluate a factory per invocation while ignoring call arguments.

    Returns:
        A callback that evaluates the typed factory anew on each invocation.

    """

    def invoke(*_args: object, **_kwargs: object) -> T:
        return factory()

    return invoke
