import pytest

from australian_health_policy_atlas.source_registry import validate_registry


def base_source() -> dict[str, object]:
    return {
        "source_id": "x",
        "jurisdiction": "QLD",
        "url": "https://health.test/x",
        "authority": "official",
    }


def test_schema_version_rejected() -> None:
    with pytest.raises(ValueError, match="schema"):
        validate_registry({"schema_version": "2", "sources": []})


def test_duplicate_rejected() -> None:
    x = base_source()
    with pytest.raises(ValueError, match="duplicate"):
        validate_registry({"schema_version": "1.0", "sources": [x, dict(x)]})


def test_unknown_jurisdiction_rejected() -> None:
    x = base_source()
    x["jurisdiction"] = "XX"
    with pytest.raises(ValueError, match="jurisdiction"):
        validate_registry({"schema_version": "1.0", "sources": [x]})


def test_http_rejected() -> None:
    x = base_source()
    x["url"] = "http://health.test/x"
    with pytest.raises(ValueError, match="https"):
        validate_registry({"schema_version": "1.0", "sources": [x]})


def test_nonofficial_rejected() -> None:
    x = base_source()
    x["authority"] = "unofficial"
    with pytest.raises(ValueError, match="official"):
        validate_registry({"schema_version": "1.0", "sources": [x]})
