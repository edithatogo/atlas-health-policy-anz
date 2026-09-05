from __future__ import annotations

import pytest

from australian_health_policy_atlas import nlp as nlp_module


def test_spacy_unavailable_is_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(nlp_module, "spacy_available", lambda: False)
    result = nlp_module.analyse_with_spacy("Nurses must escalate care.")
    assert result.available is False
    assert result.independent_method is False
    assert result.reason_codes == ("spacy_not_installed",)


def test_phrase_patterns_ignore_blank_values() -> None:
    assert nlp_module._phrase_patterns("X", ["a", " "]) == [
        {"label": "X", "pattern": "a"}
    ]


def test_spacy_blank_pipeline_when_installed() -> None:
    if not nlp_module.spacy_available():
        return
    result = nlp_module.analyse_with_spacy(
        "Registered nurses must escalate clinical deterioration. NSQHS applies.",
        concept_phrases=["clinical deterioration"],
        role_phrases=["Registered nurses"],
    )
    assert result.available is True
    assert result.statistical is False
    assert result.independent_method is False
    labels = {span.label for span in result.spans}
    assert "MODALITY" in labels
    assert "POLICY_CONCEPT" in labels
    assert "POLICY_ROLE" in labels
    assert "FRAMEWORK" in labels
    assert result.sentences


def test_spacy_missing_named_model_is_bounded() -> None:
    if not nlp_module.spacy_available():
        return
    result = nlp_module.analyse_with_spacy(
        "Nurses must escalate care.",
        model_name="atlas_model_that_does_not_exist_12345",
    )
    assert result.available is False
    assert result.reason_codes == ("spacy_model_unavailable",)


def test_spacy_statistical_flag_with_injected_pipeline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if not nlp_module.spacy_available():
        return
    import spacy

    monkeypatch.setattr(spacy, "load", lambda _name: spacy.blank("en"))
    result = nlp_module.analyse_with_spacy(
        "Nurses should escalate care.",
        model_name="fake-statistical-model",
    )
    assert result.available is True
    assert result.statistical is True
    assert result.independent_method is True
    assert (
        "statistical_pipeline_requires_benchmark_qualification" in result.reason_codes
    )
    assert result.spans[0].as_dict()["label"] == "MODALITY"
    assert result.sentences[0].as_dict()["text"] == "Nurses should escalate care."
