from typing import TypedDict

import pytest

from australian_health_policy_atlas.microtasks import (
    EvidenceInput,
    compile_packet,
)


class PacketArguments(TypedDict):
    output_schema: dict[str, object]
    invariants: list[str]
    stop_conditions: list[str]
    abstention_codes: list[str]
    task_id: str
    skill_id: str
    objective: str
    open_question: str


BASE: PacketArguments = PacketArguments(
    task_id="t",
    skill_id="s",
    objective="o",
    open_question="q",
    output_schema={"type": "object"},
    invariants=["i"],
    stop_conditions=["s"],
    abstention_codes=["evidence_missing"],
)


def test_unknown_route_rejected() -> None:
    with pytest.raises(ValueError, match="unknown model route"):
        compile_packet(
            **BASE, evidence=[EvidenceInput("a", "b", "c")], model_route="bad"
        )


def test_unknown_abstention_rejected() -> None:
    values = BASE.copy()
    values["abstention_codes"] = ["bad"]
    with pytest.raises(ValueError, match="unknown abstention"):
        compile_packet(**values, evidence=[EvidenceInput("a", "b", "c")])


def test_empty_evidence_rejected() -> None:
    with pytest.raises(ValueError, match="at least one"):
        compile_packet(**BASE, evidence=[])


def test_budget_rejected() -> None:
    with pytest.raises(ValueError, match="budget"):
        compile_packet(
            **BASE, evidence=[EvidenceInput("a", "b", "c")], evidence_tokens=6001
        )
