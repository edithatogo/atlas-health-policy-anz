"""Compile bounded, content-addressed tasks for tiny/local models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .hashing import sha256_json, sha256_text


ABSTENTION_CODES = frozenset({
    "evidence_missing",
    "definition_missing",
    "scope_unclear",
    "authority_unclear",
    "temporal_mismatch",
    "exception_reference_missing",
    "cross_reference_needed",
    "ambiguous_modality",
    "conflicting_evidence",
    "unsupported_task",
    "context_budget_exceeded",
})

ROUTES = frozenset({
    "deterministic_rule",
    "lexical_or_structural_model",
    "tiny_local_model",
    "small_local_model",
    "independent_model_triangulation",
    "larger_model_fallback",
})


@dataclass(frozen=True, slots=True)
class EvidenceInput:
    source_id: str
    span_id: str
    text: str
    context_role: str = "primary"

    def as_packet_ref(self) -> dict[str, str]:
        return {
            "source_id": self.source_id,
            "span_id": self.span_id,
            "sha256": sha256_text(self.text),
            "text": self.text,
            "context_role": self.context_role,
        }


def compile_packet(
    *,
    task_id: str,
    skill_id: str,
    objective: str,
    open_question: str,
    evidence: Iterable[EvidenceInput],
    output_schema: dict[str, Any],
    invariants: Iterable[str],
    stop_conditions: Iterable[str],
    abstention_codes: Iterable[str],
    model_route: str = "tiny_local_model",
    prompt_version: str = "v1",
    instruction_tokens: int = 400,
    evidence_tokens: int = 2400,
    output_tokens: int = 500,
) -> dict[str, Any]:
    if model_route not in ROUTES:
        raise ValueError(f"unknown model route: {model_route}")
    abstentions = list(abstention_codes)
    unknown = sorted(set(abstentions) - ABSTENTION_CODES)
    if unknown:
        raise ValueError(f"unknown abstention codes: {unknown}")
    refs = [item.as_packet_ref() for item in evidence]
    if not refs:
        raise ValueError("at least one evidence span is required")
    if not (1 <= instruction_tokens <= 900 and 1 <= evidence_tokens <= 6000 and 1 <= output_tokens <= 1000):
        raise ValueError("context budget exceeds governed limits")
    packet: dict[str, Any] = {
        "packet_version": "1.0",
        "task_id": task_id,
        "skill_id": skill_id,
        "objective": objective,
        "open_question": open_question,
        "allowed_inputs": ["evidence_refs"],
        "evidence_refs": refs,
        "invariants": list(invariants),
        "output_schema": output_schema,
        "stop_conditions": list(stop_conditions),
        "abstention_codes": abstentions,
        "context_budget": {
            "instruction_tokens": instruction_tokens,
            "evidence_tokens": evidence_tokens,
            "output_tokens": output_tokens,
        },
        "prompt_version": prompt_version,
        "model_route": model_route,
    }
    packet["packet_sha256"] = sha256_json(packet)
    return packet


def render_prompt(packet: dict[str, Any]) -> str:
    """Render a compact prompt whose facts are entirely packet-local."""
    evidence_lines = []
    for ref in packet["evidence_refs"]:
        evidence_lines.append(f"[{ref['span_id']}] ({ref.get('context_role', 'primary')}) {ref['text']}")
    invariants = "\n".join(f"- {item}" for item in packet["invariants"])
    abstentions = ", ".join(packet["abstention_codes"])
    return (
        f"TASK: {packet['objective']}\n"
        f"QUESTION: {packet['open_question']}\n\n"
        f"EVIDENCE:\n" + "\n".join(evidence_lines) + "\n\n"
        f"INVARIANTS:\n{invariants}\n\n"
        f"Return only JSON matching the supplied schema. "
        f"If unsupported, return an abstention using one of: {abstentions}."
    )
