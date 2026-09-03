from australian_health_policy_atlas.domain import EvidenceState
from australian_health_policy_atlas.platinum import baseline_relationship, jaccard_similarity, qualify_comparability


def test_modality_mismatch_is_material_even_when_text_similar() -> None:
    relationship, state, reasons = baseline_relationship(
        "Nurses must escalate care within 30 minutes",
        "Nurses should escalate care within 30 minutes",
        left_modality="must",
        right_modality="should",
        threshold=0.5,
    )
    assert relationship == "material_difference"
    assert state is EvidenceState.VERIFIED
    assert "modality_mismatch" in reasons


def test_missing_scope_blocks_comparability() -> None:
    result = qualify_comparability(
        left_scope=None,
        right_scope="acute care",
        left_authority="policy",
        right_authority="policy",
        left_valid=True,
        right_valid=True,
    )
    assert not result.comparable
    assert "scope_unclear" in result.reasons


def test_similarity_is_symmetric() -> None:
    assert jaccard_similarity("a b c", "b c d") == jaccard_similarity("b c d", "a b c")
