import sys
from types import SimpleNamespace

import pytest

from australian_health_policy_atlas.parsers import parse_file
from australian_health_policy_atlas.platinum import baseline_relationship


def test_cas_html_routes_without_extension(tmp_path):
    cas = tmp_path / ("a" * 64)
    cas.write_text("<p>Nurses must document care.</p>")
    result = parse_file(
        cas,
        source_id="s",
        media_type="text/html; charset=utf-8",
        source_uri="https://health.test/policy",
    )
    assert result.parser_id == "stdlib-html-v1"
    assert result.segments[0].text == "Nurses must document care."
    result = parse_file(
        cas, source_id="s", source_uri="https://health.test/policy.html"
    )
    assert result.parser_id == "stdlib-html-v1"
    with pytest.raises(ValueError, match="disagree"):
        parse_file(
            cas,
            source_id="s",
            media_type="text/html",
            source_uri="https://health.test/policy.pdf",
        )


def test_docx_tables_have_loss_warning(tmp_path, monkeypatch):
    file = tmp_path / "s.docx"
    file.write_bytes(b"fixture")
    monkeypatch.setitem(
        sys.modules,
        "docx",
        SimpleNamespace(
            Document=lambda _p: SimpleNamespace(
                paragraphs=[SimpleNamespace(text="Paragraph")], tables=[object()]
            )
        ),
    )
    result = parse_file(file, source_id="s")
    assert "docx_tables_not_extracted" in result.warnings


def test_optional_parsers_missing_or_mocked(tmp_path, monkeypatch):
    file = tmp_path / "s.pdf"
    file.write_bytes(b"fixture")
    monkeypatch.setitem(sys.modules, "pymupdf", None)
    monkeypatch.setitem(sys.modules, "pypdf", None)
    with pytest.raises(RuntimeError, match="PDF parsing"):
        parse_file(file, source_id="s")
    monkeypatch.setitem(
        sys.modules,
        "pymupdf",
        SimpleNamespace(
            open=lambda _p: [SimpleNamespace(get_text=lambda _kind: "text")]
        ),
    )
    assert parse_file(file, source_id="s").parser_id == "pymupdf-v1"
    file = tmp_path / "s.docx"
    file.write_bytes(b"fixture")
    monkeypatch.setitem(sys.modules, "docx", None)
    with pytest.raises(RuntimeError, match="DOCX parsing"):
        parse_file(file, source_id="s")


def test_missing_evidence_and_bad_threshold_abstain():
    assert (
        baseline_relationship("", "", left_modality=None, right_modality=None)[0]
        == "not_determined"
    )
    with pytest.raises(ValueError, match="threshold"):
        baseline_relationship(
            "a", "b", left_modality=None, right_modality=None, threshold=2
        )
