"""Generated invariants supplement fixed fixtures; they are not clinical benchmarks."""

import hashlib

from hypothesis import given, strategies as st
import pytest

from australian_health_policy_atlas.domain import MedallionLayer
from australian_health_policy_atlas.hashing import canonical_json_bytes, sha256_bytes
from australian_health_policy_atlas.state_machine import promotion_gate


@pytest.mark.property
@given(st.binary(max_size=2048))
def test_hash_agrees_with_independent_stdlib_oracle(payload: bytes) -> None:
    assert sha256_bytes(payload) == hashlib.sha256(payload).hexdigest()


@pytest.mark.property
@given(st.dictionaries(st.text(max_size=30), st.integers(), max_size=20))
def test_json_is_invariant_to_key_insertion_order(value: dict[str, int]) -> None:
    reversed_value = dict(reversed(tuple(value.items())))
    assert canonical_json_bytes(value) == canonical_json_bytes(reversed_value)


@pytest.mark.property
@given(st.sets(st.sampled_from(tuple(MedallionLayer))), st.dictionaries(
    st.text(alphabet="abcdef", min_size=1, max_size=8), st.booleans(), max_size=8))
def test_silver_gate_never_compensates_for_missing_evidence(
    closed: set[MedallionLayer], evidence: dict[str, bool],
) -> None:
    decision = promotion_gate(MedallionLayer.SILVER, closed_layers=closed,
                              acceptance_results=evidence)
    expected = MedallionLayer.BRONZE in closed and bool(evidence) and all(evidence.values())
    assert decision.permitted is expected
