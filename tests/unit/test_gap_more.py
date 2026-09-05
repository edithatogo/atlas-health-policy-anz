from australian_health_policy_atlas.domain import EvidenceState, PolicyAssertion
from australian_health_policy_atlas.gap import build_gap_rows


def a(identifier: str) -> PolicyAssertion:
    return PolicyAssertion(
        identifier,
        "QLD",
        "s",
        "sp",
        "nurse",
        "must",
        "act",
        "care",
        evidence_state=EvidenceState.VERIFIED,
    )


def test_no_comparator_is_reported_not_invented() -> None:
    row = build_gap_rows([a("a")], [])[0]
    assert row.comparator_assertion_id is None
    assert row.relationship == "no_candidate_found"
