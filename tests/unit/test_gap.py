from australian_health_policy_atlas.domain import EvidenceState, PolicyAssertion
from australian_health_policy_atlas.gap import build_gap_rows


def assertion(identifier: str, modality: str, action: str) -> PolicyAssertion:
    return PolicyAssertion(
        assertion_id=identifier,
        jurisdiction="QLD",
        source_id="s",
        source_span_id="x",
        actor="nurse",
        modality=modality,
        action=action,
        object="care",
        evidence_state=EvidenceState.VERIFIED,
    )


def test_gap_detects_material_modality_difference() -> None:
    rows = build_gap_rows([assertion("a", "must", "escalate")], [assertion("b", "should", "escalate")])
    assert rows[0].relationship == "material_difference"
