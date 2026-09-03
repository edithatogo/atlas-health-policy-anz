import pytest

from australian_health_policy_atlas.domain import MedallionLayer, ReleaseStatus, WorkStatus
from australian_health_policy_atlas.state_machine import InvalidTransition, promotion_gate, transition_release, transition_work


def test_work_state_cannot_skip_to_verified() -> None:
    with pytest.raises(InvalidTransition):
        transition_work(WorkStatus.QUEUED, WorkStatus.VERIFIED)


def test_release_state_is_finite() -> None:
    assert transition_release(ReleaseStatus.PLANNED, ReleaseStatus.EXECUTING) is ReleaseStatus.EXECUTING
    with pytest.raises(InvalidTransition):
        transition_release(ReleaseStatus.CLOSED, ReleaseStatus.EXECUTING)


def test_silver_requires_closed_bronze() -> None:
    denied = promotion_gate(MedallionLayer.SILVER, closed_layers=set(), acceptance_results={"lineage": True})
    assert not denied.permitted
    allowed = promotion_gate(MedallionLayer.SILVER, closed_layers={MedallionLayer.BRONZE}, acceptance_results={"lineage": True})
    assert allowed.permitted
