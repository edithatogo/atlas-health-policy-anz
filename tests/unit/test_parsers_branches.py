from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

from australian_health_policy_atlas.parsers import parse_file


def test_parse_text_html_and_unsupported(tmp_path: Path) -> None:
    txt = tmp_path / "x.txt"; txt.write_text("A", encoding="utf-8")
    html = tmp_path / "x.html"; html.write_text("<p>B</p>", encoding="utf-8")
    assert parse_file(txt, source_id="t").parser_id == "plain-text-v1"
    assert parse_file(html, source_id="h").parser_id == "stdlib-html-v1"
    bad = tmp_path / "x.bin"; bad.write_bytes(b"x")
    with pytest.raises(ValueError, match="unsupported"):
        parse_file(bad, source_id="b")


def test_pdf_fallback_to_fake_pypdf(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pdf = tmp_path / "x.pdf"; pdf.write_bytes(b"fake")
    monkeypatch.setitem(sys.modules, "pymupdf", None)
    fake = types.ModuleType("pypdf")
    class Page:
        def extract_text(self) -> str: return "Nurse must act."
    class Reader:
        def __init__(self, _path: str) -> None: self.pages = [Page()]
    fake.PdfReader = Reader  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "pypdf", fake)
    result = parse_file(pdf, source_id="p")
    assert result.parser_id == "pypdf-v1"
    assert result.segments


def test_docx_fake_module(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "x.docx"; path.write_bytes(b"fake")
    fake = types.ModuleType("docx")
    class Paragraph:
        def __init__(self, text: str) -> None: self.text = text
    class Doc:
        paragraphs = [Paragraph("Nurse should act.")]
    fake.Document = lambda _path: Doc()  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "docx", fake)
    result = parse_file(path, source_id="d")
    assert result.parser_id == "python-docx-v1"
