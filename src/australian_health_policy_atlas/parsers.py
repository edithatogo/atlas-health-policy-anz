"""Format router with dependency-free core and optional qualified parser hooks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from .silver import SilverSegment, normalize_html, normalize_text


@dataclass(frozen=True, slots=True)
class ParseResult:
    source_id: str
    parser_id: str
    segments: tuple[SilverSegment, ...]
    warnings: tuple[str, ...] = ()


def parse_file(path: str | Path, *, source_id: str, media_type: str | None = None,
               source_uri: str | None = None) -> ParseResult:
    source = Path(path)
    suffix = source.suffix.lower()
    types = {"application/pdf": ".pdf", "text/html": ".html", "application/xhtml+xml": ".html",
        "text/plain": ".txt", "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx"}
    hinted = Path(urlsplit(source_uri).path).suffix.lower() if source_uri else ""
    mime_suffix = types.get((media_type or "").split(";", 1)[0].lower())
    if mime_suffix:
        if hinted in {".pdf", ".docx"} and hinted != mime_suffix:
            raise ValueError("source URI and captured media type disagree; inspect original bytes")
        suffix = mime_suffix
    elif hinted:
        suffix = hinted
    if suffix in {".txt", ".md", ".csv", ".json", ".xml"}:
        text = source.read_text(encoding="utf-8", errors="replace")
        return ParseResult(source_id, "plain-text-v1", tuple(normalize_text(source_id, text)))
    if suffix in {".html", ".htm"}:
        text = source.read_text(encoding="utf-8", errors="replace")
        return ParseResult(source_id, "stdlib-html-v1", tuple(normalize_html(source_id, text)))
    if suffix == ".pdf":
        return _parse_pdf_optional(source, source_id)
    if suffix == ".docx":
        return _parse_docx_optional(source, source_id)
    raise ValueError(f"unsupported document format: {suffix or '<none>'}")


def _parse_pdf_optional(path: Path, source_id: str) -> ParseResult:
    try:
        import pymupdf  # type: ignore[import-not-found]
    except ImportError:
        try:
            import pypdf  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError("PDF parsing requires a qualified optional parser: pymupdf or pypdf") from exc
        reader = pypdf.PdfReader(str(path))
        blocks = [page.extract_text() or "" for page in reader.pages]
        segments: list[SilverSegment] = []
        for page_number, block in enumerate(blocks, 1):
            for segment in normalize_text(f"{source_id}.p{page_number}", block, parser_id="pypdf-v1"):
                segments.append(segment)
        return ParseResult(source_id, "pypdf-v1", tuple(segments))
    document = pymupdf.open(path)
    segments = []
    for page_number, page in enumerate(document, 1):
        block = page.get_text("text")
        for segment in normalize_text(f"{source_id}.p{page_number}", block, parser_id="pymupdf-v1"):
            segments.append(segment)
    return ParseResult(source_id, "pymupdf-v1", tuple(segments))


def _parse_docx_optional(path: Path, source_id: str) -> ParseResult:
    try:
        import docx  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError("DOCX parsing requires the qualified optional parser python-docx") from exc
    document = docx.Document(path)
    text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    warnings = ("docx_tables_not_extracted",) if getattr(document, "tables", ()) else ()
    return ParseResult(source_id, "python-docx-v1", tuple(normalize_text(source_id, text, parser_id="python-docx-v1")), warnings)
