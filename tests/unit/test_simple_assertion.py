from australian_health_policy_atlas.gold import extract_simple_assertion_fields


def test_simple_assertion_extracts_actor_action_object_and_time() -> None:
    result = extract_simple_assertion_fields("The registered nurse must notify the medical officer within 30 minutes.")
    assert result.deterministic
    assert result.actor == "The registered nurse"
    assert result.modality == "must"
    assert result.action == "notify"
    assert result.object == "the medical officer"
    assert result.timeframe == "within 30 minutes"


def test_complex_clause_abstains_from_semantic_fields() -> None:
    result = extract_simple_assertion_fields("Where clinically appropriate, staff must, after review, notify the service.")
    assert not result.deterministic
    assert result.modality == "must"
