from australian_health_policy_atlas.microtasks import EvidenceInput, compile_packet, render_prompt
from australian_health_policy_atlas.verification import verify_model_output, verify_packet_evidence


SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["modality", "source_span_id"],
    "properties": {
        "modality": {"enum": ["must", "should", "may", "must_not"]},
        "source_span_id": {"type": "string"},
    },
}


def packet() -> dict[str, object]:
    return compile_packet(
        task_id="t1",
        skill_id="modality",
        objective="Classify modality",
        open_question="What is the normative modality?",
        evidence=[EvidenceInput("source", "s1", "The nurse must escalate care.")],
        output_schema=SCHEMA,
        invariants=["Use supplied evidence only."],
        stop_conditions=["A supported modality is found."],
        abstention_codes=["ambiguous_modality", "evidence_missing"],
    )


def test_packet_is_content_addressed_and_evidence_validates() -> None:
    value = packet()
    assert len(str(value["packet_sha256"])) == 64
    verify_packet_evidence(value)


def test_model_output_must_point_to_supplied_span() -> None:
    value = packet()
    verify_model_output(value, {"modality": "must", "source_span_id": "s1"})


def test_render_prompt_is_bounded_and_self_contained() -> None:
    text = render_prompt(packet())
    assert "The nurse must escalate care." in text
    assert "Return only JSON" in text
