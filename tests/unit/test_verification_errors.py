import pytest

from australian_health_policy_atlas.hashing import sha256_text
from australian_health_policy_atlas.records import record, records
from australian_health_policy_atlas.verification import (
    VerificationError,
    verify_model_output,
    verify_output_minimal,
    verify_packet_evidence,
)


def base_packet() -> dict[str, object]:
    return {
        "evidence_refs": [
            {"span_id": "s1", "text": "abc", "sha256": sha256_text("abc")}
        ],
        "output_schema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["name", "count", "score"],
            "properties": {
                "name": {"type": "string", "enum": ["x"]},
                "count": {"type": "integer"},
                "score": {"type": "number"},
            },
        },
    }


def test_evidence_hash_mismatch() -> None:
    packet = base_packet()
    records(packet["evidence_refs"])[0]["sha256"] = "0" * 64
    with pytest.raises(VerificationError, match="hash mismatch"):
        verify_packet_evidence(packet)


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ("not-object", "must be an object"),
        ({"name": "x"}, "missing required"),
        ({"name": "x", "count": 1, "score": 1, "extra": 2}, "unexpected fields"),
        ({"name": "y", "count": 1, "score": 1}, "outside allowed enum"),
        ({"name": 2, "count": 1, "score": 1}, "outside allowed enum"),
        ({"name": "x", "count": True, "score": 1}, "must be an integer"),
        ({"name": "x", "count": 1, "score": True}, "must be numeric"),
    ],
)
def test_minimal_schema_failures(value: object, message: str) -> None:
    with pytest.raises(VerificationError, match=message):
        verify_output_minimal(record(base_packet()["output_schema"]), value)


def test_source_span_must_exist() -> None:
    packet = base_packet()
    packet["output_schema"] = {
        "type": "object",
        "required": ["span_id"],
        "properties": {"span_id": {"type": "string"}},
    }
    with pytest.raises(VerificationError, match="does not reference"):
        verify_model_output(packet, {"span_id": "missing"})
