"""Compile bounded, content-addressed tasks for tiny/local models."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping


from dataclasses import dataclass
from typing import NotRequired, TypedDict, Unpack

from .hashing import sha256_json, sha256_text
from .records import records, strings

MAX_INSTRUCTION_TOKENS = 900
MAX_EVIDENCE_TOKENS = 6000
MAX_OUTPUT_TOKENS = 1000


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
    """One exact evidence span supplied to a bounded model task."""

    source_id: str
    span_id: str
    text: str
    context_role: str = "primary"

    def as_packet_ref(self) -> dict[str, str]:
        """Return exact text, identifiers and the evidence text hash for a model packet.

        Returns:
            A source-span reference whose text is bound to its SHA-256 hash.

        """
        return {
            "source_id": self.source_id,
            "span_id": self.span_id,
            "sha256": sha256_text(self.text),
            "text": self.text,
            "context_role": self.context_role,
        }


class PacketOptions(TypedDict):
    """Explicit schema, invariants and optional bounded model-routing controls."""

    output_schema: Mapping[str, object]
    invariants: Iterable[str]
    stop_conditions: Iterable[str]
    abstention_codes: Iterable[str]
    model_route: NotRequired[str]
    prompt_version: NotRequired[str]
    instruction_tokens: NotRequired[int]
    evidence_tokens: NotRequired[int]
    output_tokens: NotRequired[int]


def compile_packet(
    *,
    task_id: str,
    skill_id: str,
    objective: str,
    open_question: str,
    evidence: Iterable[EvidenceInput],
    **options: Unpack[PacketOptions],
) -> dict[str, object]:
    """Compile one evidence-bounded task, validating its route and token limits.

    Returns:
        The bounded task packet and its canonical content hash.

    Raises:
        ValueError: Routing, evidence, abstentions or token budgets are invalid.

    """
    model_route = options.get("model_route", "tiny_local_model")
    instruction_tokens = options.get("instruction_tokens", 400)
    evidence_tokens = options.get("evidence_tokens", 2400)
    output_tokens = options.get("output_tokens", 500)
    if model_route not in ROUTES:
        message = f"unknown model route: {model_route}"
        raise ValueError(message)
    abstentions = list(options["abstention_codes"])
    unknown = sorted(set(abstentions) - ABSTENTION_CODES)
    if unknown:
        message = f"unknown abstention codes: {unknown}"
        raise ValueError(message)
    refs = [item.as_packet_ref() for item in evidence]
    if not refs:
        message = "at least one evidence span is required"
        raise ValueError(message)
    if not (
        1 <= instruction_tokens <= MAX_INSTRUCTION_TOKENS
        and 1 <= evidence_tokens <= MAX_EVIDENCE_TOKENS
        and 1 <= output_tokens <= MAX_OUTPUT_TOKENS
    ):
        message = "context budget exceeds governed limits"
        raise ValueError(message)
    packet: dict[str, object] = {
        "packet_version": "1.0",
        "task_id": task_id,
        "skill_id": skill_id,
        "objective": objective,
        "open_question": open_question,
        "allowed_inputs": ["evidence_refs"],
        "evidence_refs": refs,
        "invariants": list(options["invariants"]),
        "output_schema": options["output_schema"],
        "stop_conditions": list(options["stop_conditions"]),
        "abstention_codes": abstentions,
        "context_budget": {
            "instruction_tokens": instruction_tokens,
            "evidence_tokens": evidence_tokens,
            "output_tokens": output_tokens,
        },
        "prompt_version": options.get("prompt_version", "v1"),
        "model_route": model_route,
    }
    packet["packet_sha256"] = sha256_json(packet)
    return packet


def render_prompt(packet: Mapping[str, object]) -> str:
    """Render a compact prompt whose facts are entirely packet-local.

    Returns:
        The evidence-local prompt rendered from the supplied packet.

    """
    evidence_lines = [
        f"[{ref['span_id']}] ({ref.get('context_role', 'primary')}) {ref['text']}"
        for ref in records(packet["evidence_refs"])
    ]
    invariants = "\n".join(f"- {item}" for item in strings(packet["invariants"]))
    abstentions = ", ".join(strings(packet["abstention_codes"]))
    return (
        f"TASK: {packet['objective']}\n"
        f"QUESTION: {packet['open_question']}\n\n"
        f"EVIDENCE:\n" + "\n".join(evidence_lines) + "\n\n"
        f"INVARIANTS:\n{invariants}\n\n"
        f"Return only JSON matching the supplied schema. "
        f"If unsupported, return an abstention using one of: {abstentions}."
    )
