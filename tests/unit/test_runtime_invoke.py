from __future__ import annotations

from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    import pytest


import json

from australian_health_policy_atlas.hashing import sha256_text
from australian_health_policy_atlas.runtime import llamacpp
from tests.support import ignoring_arguments


class Response:
    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    @staticmethod
    def read(_amount: int) -> bytes:
        return json.dumps({
            "choices": [
                {
                    "message": {
                        "content": json.dumps({
                            "modality": "must",
                            "source_span_id": "s1",
                        })
                    }
                }
            ]
        }).encode()


def test_invoke_loopback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(llamacpp, "urlopen", ignoring_arguments(Response))
    packet = {
        "objective": "x",
        "open_question": "q",
        "invariants": ["i"],
        "abstention_codes": ["evidence_missing"],
        "evidence_refs": [
            {
                "span_id": "s1",
                "source_id": "x",
                "text": "Nurse must act.",
                "sha256": sha256_text("Nurse must act."),
            }
        ],
        "output_schema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["modality", "source_span_id"],
            "properties": {
                "modality": {"enum": ["must"]},
                "source_span_id": {"type": "string"},
            },
        },
    }
    receipt = llamacpp.invoke_openai_compatible(packet)
    assert receipt.output["modality"] == "must"
