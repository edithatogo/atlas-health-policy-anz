"""Optional spaCy NLP projection used as non-authoritative triangulation evidence.

The canonical policy facts remain Silver/Gold records.  This module produces
rebuildable NLP features with exact character offsets.  Rule-only spaCy output
is *not* counted as an independent method from deterministic patterns; a
qualified statistical pipeline may contribute distinct method evidence only
when its exact model manifest and benchmark are recorded.
"""

from __future__ import annotations

import importlib.util
from dataclasses import asdict, dataclass
from typing import Any, Iterable


@dataclass(frozen=True, slots=True)
class NlpSpan:
    label: str
    text: str
    start_char: int
    end_char: int
    method: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class NlpSentence:
    text: str
    start_char: int
    end_char: int

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class NlpAnalysis:
    engine: str
    model: str
    available: bool
    statistical: bool
    independent_method: bool
    sentences: tuple[NlpSentence, ...]
    spans: tuple[NlpSpan, ...]
    lemmas: tuple[str, ...]
    reason_codes: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "engine": self.engine,
            "model": self.model,
            "available": self.available,
            "statistical": self.statistical,
            "independent_method": self.independent_method,
            "sentences": [item.as_dict() for item in self.sentences],
            "spans": [item.as_dict() for item in self.spans],
            "lemmas": list(self.lemmas),
            "reason_codes": list(self.reason_codes),
        }


_DEFAULT_PATTERNS: tuple[dict[str, Any], ...] = (
    {"label": "MODALITY", "pattern": [{"LOWER": "must"}, {"LOWER": "not"}]},
    {"label": "MODALITY", "pattern": [{"LOWER": "must"}]},
    {"label": "MODALITY", "pattern": [{"LOWER": "shall"}, {"LOWER": "not"}]},
    {"label": "MODALITY", "pattern": [{"LOWER": "shall"}]},
    {"label": "MODALITY", "pattern": [{"LOWER": "should"}]},
    {"label": "MODALITY", "pattern": [{"LOWER": "may"}]},
    {"label": "JURISDICTION", "pattern": "New Zealand"},
    {"label": "JURISDICTION", "pattern": "Aotearoa"},
    {"label": "FRAMEWORK", "pattern": "Ngā Paerewa"},
    {"label": "FRAMEWORK", "pattern": "Nga Paerewa"},
    {"label": "FRAMEWORK", "pattern": "NZS 8134:2021"},
    {"label": "FRAMEWORK", "pattern": "Te Tiriti o Waitangi"},
    {"label": "FRAMEWORK", "pattern": "Health Information Privacy Code"},
    {"label": "FRAMEWORK", "pattern": "NSQHS"},
    {"label": "FRAMEWORK", "pattern": "National Safety and Quality Health Service Standards"},
    {"label": "JURISDICTION", "pattern": "Queensland"},
    {"label": "JURISDICTION", "pattern": "New South Wales"},
    {"label": "JURISDICTION", "pattern": "Victoria"},
    {"label": "JURISDICTION", "pattern": "South Australia"},
    {"label": "JURISDICTION", "pattern": "Western Australia"},
    {"label": "JURISDICTION", "pattern": "Tasmania"},
    {"label": "JURISDICTION", "pattern": "Northern Territory"},
    {"label": "JURISDICTION", "pattern": "Australian Capital Territory"},
)


def spacy_available() -> bool:
    """Return whether spaCy is importable without importing it eagerly."""
    return importlib.util.find_spec("spacy") is not None


def _phrase_patterns(label: str, phrases: Iterable[str]) -> list[dict[str, str]]:
    return [{"label": label, "pattern": phrase} for phrase in phrases if phrase.strip()]


def analyse_with_spacy(
    text: str,
    *,
    model_name: str | None = None,
    concept_phrases: Iterable[str] = (),
    role_phrases: Iterable[str] = (),
) -> NlpAnalysis:
    """Project exact-offset NLP features using spaCy when available.

    A blank English pipeline is a useful deterministic tokenizer/sentence
    segmenter/entity-ruler fallback.  Because its rule features overlap with
    deterministic Atlas patterns, it is explicitly marked non-independent.
    A loaded statistical pipeline is marked as potentially independent, but it
    still requires benchmark qualification before confidence composition may
    count it as such.
    """
    if not spacy_available():
        return NlpAnalysis(
            engine="spacy",
            model=model_name or "blank-en",
            available=False,
            statistical=False,
            independent_method=False,
            sentences=(),
            spans=(),
            lemmas=(),
            reason_codes=("spacy_not_installed",),
        )

    import spacy  # type: ignore[import-not-found]

    statistical = model_name is not None
    try:
        nlp = spacy.load(model_name) if model_name else spacy.blank("en")
    except OSError:
        return NlpAnalysis(
            engine="spacy",
            model=model_name or "blank-en",
            available=False,
            statistical=False,
            independent_method=False,
            sentences=(),
            spans=(),
            lemmas=(),
            reason_codes=("spacy_model_unavailable",),
        )

    if (
        "sentencizer" not in nlp.pipe_names
        and "parser" not in nlp.pipe_names
        and "senter" not in nlp.pipe_names
    ):
        nlp.add_pipe("sentencizer")

    ruler_name = "atlas_entity_ruler"
    if ruler_name not in nlp.pipe_names:
        ruler = nlp.add_pipe("entity_ruler", name=ruler_name, config={"overwrite_ents": False})
        patterns: list[dict[str, Any]] = list(_DEFAULT_PATTERNS)
        patterns.extend(_phrase_patterns("POLICY_CONCEPT", concept_phrases))
        patterns.extend(_phrase_patterns("POLICY_ROLE", role_phrases))
        ruler.add_patterns(patterns)

    doc = nlp(text)
    sentences = tuple(NlpSentence(sent.text, sent.start_char, sent.end_char) for sent in doc.sents)
    spans = tuple(
        NlpSpan(
            ent.label_,
            ent.text,
            ent.start_char,
            ent.end_char,
            f"spacy:{model_name or 'blank-en'}:{'statistical' if statistical else 'ruler'}",
        )
        for ent in doc.ents
    )
    lemmas = tuple(
        token.lemma_.lower()
        for token in doc
        if token.is_alpha and token.lemma_ and token.lemma_ != "-PRON-"
    )
    reasons = ["spacy_exact_offset_projection"]
    if statistical:
        reasons.append("statistical_pipeline_requires_benchmark_qualification")
    else:
        reasons.append("rule_pipeline_not_independent_triangulation")
    return NlpAnalysis(
        engine="spacy",
        model=model_name or "blank-en",
        available=True,
        statistical=statistical,
        independent_method=statistical,
        sentences=sentences,
        spans=spans,
        lemmas=lemmas,
        reason_codes=tuple(reasons),
    )
