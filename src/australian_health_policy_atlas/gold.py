"""Conservative deterministic Gold assertion helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass

_MODALITY_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "must_not",
        re.compile(
            r"\b(?:must\s+not|shall\s+not|is\s+prohibited\s+from)\b", re.IGNORECASE
        ),
    ),
    (
        "must",
        re.compile(
            r"\b(?:must|shall|is\s+required\s+to|are\s+required\s+to)\b", re.IGNORECASE
        ),
    ),
    (
        "should",
        re.compile(
            r"\b(?:should|is\s+recommended\s+to|are\s+recommended\s+to)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "may",
        re.compile(
            r"\b(?:may|is\s+permitted\s+to|are\s+permitted\s+to)\b", re.IGNORECASE
        ),
    ),
)


@dataclass(frozen=True, slots=True)
class ModalityResult:
    """Detected deontic modality or an explicit ambiguity reason."""

    modality: str | None
    deterministic: bool
    reason_code: str


def classify_modality(text: str) -> ModalityResult:
    """Detect normative phrases while retaining ambiguity across distinct clauses.

    Returns:
        A phrase-derived modality or an explicit ambiguity result.

    """
    raw: list[tuple[str, int, int]] = []
    for name, pattern in _MODALITY_PATTERNS:
        raw.extend(
            (name, match.start(), match.end()) for match in pattern.finditer(text)
        )
    if not raw:
        return ModalityResult(
            None, deterministic=False, reason_code="ambiguous_modality"
        )

    # Higher-priority phrases such as "must not" suppress lower-priority
    # matches wholly contained within the same source span. Distinct clauses
    # with genuinely different modalities remain conflicting.
    kept: list[tuple[str, int, int]] = []
    for candidate in raw:
        name, start, end = candidate
        if any(
            other_name != name
            and other_start <= start
            and other_end >= end
            and _priority(other_name) < _priority(name)
            for other_name, other_start, other_end in raw
        ):
            continue
        kept.append(candidate)
    unique = {name for name, _start, _end in kept}
    if len(unique) > 1:
        return ModalityResult(
            None, deterministic=False, reason_code="conflicting_modality_signals"
        )
    return ModalityResult(
        kept[0][0], deterministic=True, reason_code="deterministic_modality_pattern"
    )


def _priority(name: str) -> int:
    order = {"must_not": 0, "must": 1, "should": 2, "may": 3}
    return order[name]


def extract_timeframe(text: str) -> str | None:
    """Return the first supported relative deadline without inferring missing timing.

    Returns:
        The observed relative deadline, or None when no supported form exists.

    """
    match = re.search(
        r"\bwithin\s+(\d+)\s+(minute|minutes|hour|hours|day|days|week|weeks)\b",
        text,
        re.IGNORECASE,
    )
    return match.group(0).lower() if match else None


@dataclass(frozen=True, slots=True)
class SimpleAssertionFields:
    """Conservative clause fields; extraction alone is not qualification."""

    actor: str | None
    action: str | None
    object: str | None
    modality: str | None
    timeframe: str | None
    deterministic: bool
    reason_code: str


def extract_simple_assertion_fields(text: str) -> SimpleAssertionFields:
    """Extract only simple actor-modal-verb-object clauses; abstain otherwise.

    Returns:
        Conservative fields and the rule or abstention reason.

    """
    modality_result = classify_modality(text)
    if modality_result.modality is None:
        return SimpleAssertionFields(
            None,
            None,
            None,
            None,
            extract_timeframe(text),
            deterministic=False,
            reason_code=modality_result.reason_code,
        )
    modal_phrases = {
        "must_not": r"must\s+not|shall\s+not|is\s+prohibited\s+from",
        "must": r"must|shall|is\s+required\s+to|are\s+required\s+to",
        "should": r"should|is\s+recommended\s+to|are\s+recommended\s+to",
        "may": r"may|is\s+permitted\s+to|are\s+permitted\s+to",
    }
    phrase = modal_phrases[modality_result.modality]
    pattern = re.compile(
        rf"^\s*(?P<actor>.+?)\s+(?:{phrase})\s+(?P<action>[A-Za-z][A-Za-z-]*)\s+(?P<object>.+?)\s*[.;]?\s*$",
        re.IGNORECASE,
    )
    match = pattern.match(text)
    if not match:
        return SimpleAssertionFields(
            None,
            None,
            None,
            modality_result.modality,
            extract_timeframe(text),
            deterministic=False,
            reason_code="complex_clause_requires_structured_extraction",
        )
    obj = match.group("object").strip()
    timeframe = extract_timeframe(obj)
    if timeframe:
        obj = re.sub(
            r"\s+within\s+\d+\s+(?:minute|minutes|hour|hours|day|days|week|weeks)\b.*$",
            "",
            obj,
            flags=re.IGNORECASE,
        ).strip()
    return SimpleAssertionFields(
        actor=match.group("actor").strip(),
        action=match.group("action").lower(),
        object=obj.rstrip(".; "),
        modality=modality_result.modality,
        timeframe=timeframe,
        deterministic=True,
        reason_code="simple_clause_pattern",
    )
