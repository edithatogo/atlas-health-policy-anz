"""Validate untrusted serialized values before exposing typed operations.

Casts here only widen an external value to ``object`` or a built-in container
of objects, after checking its container type. No cast asserts a field's schema.
Every narrower return type is established by runtime checks.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping


import json
import math
from typing import cast


def record(value: object) -> dict[str, object]:
    """Return a string-keyed dictionary after checking its container and keys.

    Returns:
        The original dictionary after checking its container and key types.

    Raises:
        TypeError: The value is not a string-keyed mapping.

    """
    if not isinstance(value, dict):
        message = "JSON object required"
        raise TypeError(message)
    items = cast("Mapping[object, object]", value)
    for key in items:
        if not isinstance(key, str):
            message = "JSON object keys must be strings"
            raise TypeError(message)
    return cast("dict[str, object]", value)


def array(value: object) -> list[object]:
    """Return a list after checking its concrete container type.

    Returns:
        The original list after checking its concrete container type.

    Raises:
        TypeError: The value is not a list.

    """
    if not isinstance(value, list):
        message = "JSON array required"
        raise TypeError(message)
    return cast("list[object]", value)


def records(value: object) -> list[dict[str, object]]:
    """Validate an array of string-keyed records and return validated shapes.

    Returns:
        Validated record references in input order; the outer list is a new list.

    """
    return [record(item) for item in array(value)]


def string(value: object) -> str:
    """Return a string without coercing malformed or missing values.

    Returns:
        The unchanged string; no coercion is performed.

    Raises:
        TypeError: The value is not a string.

    """
    if not isinstance(value, str):
        message = "string required"
        raise TypeError(message)
    return value


def optional_string(value: object) -> str | None:
    """Validate a nullable string, preserving missing optional fields.

    Returns:
        The unchanged string, or None for a missing optional field.

    """
    return None if value is None else string(value)


def strings(value: object) -> list[str]:
    """Validate an array of strings without stringifying other values.

    Returns:
        A new list containing the validated input strings in order.

    """
    return [string(item) for item in array(value)]


def integer(value: object) -> int:
    """Return an integer, excluding the boolean subclass.

    Returns:
        The unchanged integer, excluding booleans.

    Raises:
        TypeError: The value is not an integer or is a boolean.

    """
    if not isinstance(value, int) or isinstance(value, bool):
        message = "integer required"
        raise TypeError(message)
    return value


def number(value: object) -> float:
    """Return a numeric value, excluding booleans.

    Returns:
        The validated floating-point representation of a numeric input.

    Raises:
        TypeError: The value is neither an integer nor a float.

    """
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        message = "number required"
        raise TypeError(message)
    return float(value)


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            message = "duplicate JSON key"
            raise ValueError(message)
        result[key] = value
    return result


def _bad_constant(value: str) -> None:
    message = f"non-finite JSON constant: {value}"
    raise ValueError(message)


def _finite_float(value: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        message = "non-finite JSON number"
        raise ValueError(message)
    return result


def decode_json(data: str | bytes) -> object:
    """Decode strict JSON to an untrusted object for subsequent validation.

    Returns:
        Decoded values typed as untrusted objects for subsequent schema validation.

    """
    return cast(
        "object",
        json.loads(
            data,
            object_pairs_hook=_pairs,
            parse_constant=_bad_constant,
            parse_float=_finite_float,
        ),
    )
