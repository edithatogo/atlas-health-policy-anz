"""Deterministic verification for packets, spans and structured outputs."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping


from typing import cast

from .hashing import sha256_text
from .records import array, record, records, string, strings


class VerificationError(ValueError):
    """A structured output does not satisfy its explicit evidence contract."""


def verify_packet_evidence(packet: Mapping[str, object]) -> None:
    """Check every supplied span against its independently calculated digest.

    Raises:
        VerificationError: A source text does not match its recorded hash.

    """
    for ref in records(packet.get("evidence_refs", [])):
        actual = sha256_text(string(ref["text"]))
        if actual != ref["sha256"]:
            message = f"source hash mismatch for {ref['span_id']}"
            raise VerificationError(message)


def verify_exact_span(packet: Mapping[str, object], span_id: str) -> bool:
    """Return whether the identifier occurs in the supplied evidence packet.

    Returns:
        The result described above, retaining the declared return-type contract.

    """
    return any(
        ref["span_id"] == span_id for ref in records(packet.get("evidence_refs", []))
    )


def _verify_fields(schema: Mapping[str, object], output: Mapping[str, object]) -> None:
    missing = [key for key in strings(schema.get("required", [])) if key not in output]
    if missing:
        message = f"missing required fields: {missing}"
        raise VerificationError(message)
    if schema.get("additionalProperties") is False:
        allowed = set(record(schema.get("properties", {})))
        extra = sorted(set(output) - allowed)
        if extra:
            message = f"unexpected fields: {extra}"
            raise VerificationError(message)


def _verify_property(key: str, schema: Mapping[str, object], value: object) -> None:
    if "enum" in schema and value not in array(schema["enum"]):
        message = f"{key} is outside allowed enum"
        raise VerificationError(message)
    expected = schema.get("type")
    if expected == "string" and not isinstance(value, str):
        message = f"{key} must be a string"
        raise VerificationError(message)
    if expected == "integer" and (
        not isinstance(value, int) or isinstance(value, bool)
    ):
        message = f"{key} must be an integer"
        raise VerificationError(message)
    if expected == "number" and (
        not isinstance(value, (int, float)) or isinstance(value, bool)
    ):
        message = f"{key} must be numeric"
        raise VerificationError(message)


def verify_output_minimal(schema: Mapping[str, object], output: object) -> None:
    """Validate the explicitly supported subset for local/offline output checks.

    This is not a full JSON Schema implementation. Production schema qualification
    is performed by the registered JSON Schema validator and its contract tests.

    Raises:
        VerificationError: An object, required field, enum or primitive is invalid.

    """
    if schema.get("type") != "object":
        return
    if not isinstance(output, dict):
        message = "output must be an object"
        raise VerificationError(message)
    fields = record(cast("object", output))
    _verify_fields(schema, fields)
    for key, child in record(schema.get("properties", {})).items():
        if key in fields:
            _verify_property(key, record(child), fields[key])


def verify_model_output(
    packet: Mapping[str, object], output: Mapping[str, object]
) -> None:
    """Verify source hashes, supported schema rules and returned span identifiers.

    Raises:
        VerificationError: The output references evidence absent from the packet.

    """
    verify_packet_evidence(packet)
    verify_output_minimal(record(packet["output_schema"]), output)
    for key in ("source_span_id", "span_id"):
        if key in output and not verify_exact_span(packet, str(output[key])):
            message = f"{key} does not reference supplied evidence"
            raise VerificationError(message)
