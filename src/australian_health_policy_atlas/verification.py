"""Deterministic verification for packets, spans and structured outputs."""

from __future__ import annotations

from typing import Any

from .hashing import sha256_text


class VerificationError(ValueError):
    pass


def verify_packet_evidence(packet: dict[str, Any]) -> None:
    for ref in packet.get("evidence_refs", []):
        actual = sha256_text(ref["text"])
        if actual != ref["sha256"]:
            raise VerificationError(f"source hash mismatch for {ref['span_id']}")


def verify_exact_span(packet: dict[str, Any], span_id: str) -> bool:
    return any(ref["span_id"] == span_id for ref in packet.get("evidence_refs", []))


def verify_output_minimal(schema: dict[str, Any], output: Any) -> None:
    """Dependency-free subset validator for local/offline canonical checks."""
    if schema.get("type") == "object":
        if not isinstance(output, dict):
            raise VerificationError("output must be an object")
        required = schema.get("required", [])
        missing = [key for key in required if key not in output]
        if missing:
            raise VerificationError(f"missing required fields: {missing}")
        if schema.get("additionalProperties") is False:
            allowed = set(schema.get("properties", {}))
            extra = sorted(set(output) - allowed)
            if extra:
                raise VerificationError(f"unexpected fields: {extra}")
        for key, child in schema.get("properties", {}).items():
            if key not in output:
                continue
            value = output[key]
            if "enum" in child and value not in child["enum"]:
                raise VerificationError(f"{key} is outside allowed enum")
            expected_type = child.get("type")
            if expected_type == "string" and not isinstance(value, str):
                raise VerificationError(f"{key} must be a string")
            if expected_type == "integer" and (
                not isinstance(value, int) or isinstance(value, bool)
            ):
                raise VerificationError(f"{key} must be an integer")
            if expected_type == "number" and (
                not isinstance(value, (int, float)) or isinstance(value, bool)
            ):
                raise VerificationError(f"{key} must be numeric")


def verify_model_output(packet: dict[str, Any], output: dict[str, Any]) -> None:
    verify_packet_evidence(packet)
    verify_output_minimal(packet["output_schema"], output)
    for key in ("source_span_id", "span_id"):
        if key in output and not verify_exact_span(packet, str(output[key])):
            raise VerificationError(f"{key} does not reference supplied evidence")
