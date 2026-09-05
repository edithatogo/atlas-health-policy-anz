"""Narrow typed ports for the concrete pytest fixtures exercised by our tests.

These protocols declare only the fixture calls used here; they do not assert
that untested portions of third-party plugin interfaces have complete typing.
"""

from collections.abc import Callable
from typing import Protocol


class SubprocessFixture(Protocol):
    """The registered-command subset of the pytest-subprocess fp fixture."""

    def register(self, command: list[str], *, stdout: str) -> object:
        """Register one expected command and its synthetic stdout."""
        ...

    def call_count(self, command: list[str]) -> int:
        """Count executions of a registered command."""
        ...


class HashBenchmarkFixture(Protocol):
    """The typed hash-function specialization of the benchmark fixture."""

    def __call__(self, function: Callable[[bytes], str], payload: bytes, /) -> str:
        """Measure the supplied callable while retaining its actual result."""
        ...
