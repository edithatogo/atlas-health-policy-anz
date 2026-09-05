from australian_health_policy_atlas.domain import (
    ComparisonFinding,
    EvidenceState,
    MedallionLayer,
    PolicyAssertion,
    ReleaseReceipt,
    ReleaseStatus,
)


def test_domain_serialization_uses_string_evidence_states() -> None:
    assertion = PolicyAssertion("a", "QLD", "s", "sp", None, None, None, None)
    assert assertion.as_dict()["evidence_state"] == "A3"
    finding = ComparisonFinding("f", "a", "b", "x", EvidenceState.VERIFIED, ())
    assert finding.as_dict()["evidence_state"] == "A0"
    receipt = ReleaseReceipt(
        "r",
        MedallionLayer.BRONZE,
        ReleaseStatus.QUALIFIED,
        "a",
        "b",
        {},
        EvidenceState.VERIFIED,
        (),
    )
    value = receipt.as_dict()
    assert value["layer"] == "bronze"
    assert value["status"] == "qualified"
