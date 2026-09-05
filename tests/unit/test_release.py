from australian_health_policy_atlas.domain import EvidenceState, MedallionLayer, ReleaseStatus
from australian_health_policy_atlas.release import qualify_release


def test_release_qualifies_when_predecessor_and_acceptance_pass() -> None:
    receipt = qualify_release(
        release_id="silver-v1",
        layer=MedallionLayer.SILVER,
        input_manifest={"a": 1},
        output_manifest={"b": 2},
        acceptance_results={"lineage": True, "rebuild": True},
        closed_layers={MedallionLayer.BRONZE},
    )
    assert receipt.status is ReleaseStatus.QUALIFIED
    assert receipt.evidence_state is EvidenceState.VERIFIED


def test_release_remains_candidate_on_failed_gate() -> None:
    receipt = qualify_release(
        release_id="silver-v1",
        layer=MedallionLayer.SILVER,
        input_manifest={},
        output_manifest={},
        acceptance_results={"lineage": False},
        closed_layers={MedallionLayer.BRONZE},
    )
    assert receipt.status is ReleaseStatus.CANDIDATE
