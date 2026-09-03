from australian_health_policy_atlas.domain import EvidenceState
from australian_health_policy_atlas.platinum import baseline_relationship, jaccard_similarity, qualify_comparability


def test_empty_similarity_cases() -> None:
    assert jaccard_similarity("", "") == 1.0
    assert jaccard_similarity("a", "") == 0.0


def test_candidate_equivalent_and_not_equivalent() -> None:
    relationship, state, _ = baseline_relationship("a b c", "a b c", left_modality="must", right_modality="must", threshold=0.5)
    assert relationship == "candidate_equivalent"
    assert state is EvidenceState.SUPPORTED_NEEDS_VERIFICATION
    relationship2, _, _ = baseline_relationship("a", "z", left_modality=None, right_modality=None, threshold=0.5)
    assert relationship2 == "not_equivalent"


def test_temporal_and_authority_failures() -> None:
    result = qualify_comparability(left_scope="x", right_scope="y", left_authority=None, right_authority="p", left_valid=False, right_valid=True)
    assert set(result.reasons) == {"temporal_mismatch", "authority_unclear"}
