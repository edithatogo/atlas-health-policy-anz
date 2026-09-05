from australian_health_policy_atlas.gold import classify_modality, extract_simple_assertion_fields


def test_no_modality_and_conflicting_distinct_clauses() -> None:
    assert classify_modality("Clinicians review care.").modality is None
    conflict = classify_modality("Nurses must document care and doctors should review it.")
    assert conflict.modality is None
    assert conflict.reason_code == "conflicting_modality_signals"


def test_simple_extractor_without_modality_abstains() -> None:
    result = extract_simple_assertion_fields("Clinicians review care.")
    assert result.modality is None
