"""Format router with dependency-free core and optional qualified parser hooks."""

from __future__ import annotations

import importlib
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, cast, runtime_checkable
from urllib.parse import urlsplit

from .records import optional_string, string
from .silver import SilverSegment, normalize_html, normalize_text


@dataclass(frozen=True, slots=True)
class ParseResult:
    """Parser identity, projected segments and explicit extraction limitations."""

    source_id: str
    parser_id: str
    segments: tuple[SilverSegment, ...]
    warnings: tuple[str, ...] = ()


def parse_file(
    path: str | Path,
    *,
    source_id: str,
    media_type: str | None = None,
    source_uri: str | None = None,
) -> ParseResult:
    """Route the source by MIME type and URI, preserving parser limitations.

    Returns:
        Projected segments, exact parser identity and extraction warnings.

    Raises:
        ValueError: The supplied data violates the function's documented validation
        contract.

    """
    source = Path(path)
    suffix = source.suffix.lower()
    types = {
        "application/pdf": ".pdf",
        "text/html": ".html",
        "application/xhtml+xml": ".html",
        "text/plain": ".txt",
        (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ): ".docx",
    }
    hinted = Path(urlsplit(source_uri).path).suffix.lower() if source_uri else ""
    mime_suffix = types.get((media_type or "").split(";", 1)[0].lower())
    if mime_suffix:
        if hinted in {".pdf", ".docx"} and hinted != mime_suffix:
            message = (
                "source URI and captured media type disagree; inspect original bytes"
            )
            raise ValueError(message)
        suffix = mime_suffix
    elif hinted:
        suffix = hinted
    if suffix in {".txt", ".md", ".csv", ".json", ".xml"}:
        text = source.read_text(encoding="utf-8", errors="replace")
        return ParseResult(
            source_id, "plain-text-v1", tuple(normalize_text(source_id, text))
        )
    if suffix in {".html", ".htm"}:
        text = source.read_text(encoding="utf-8", errors="replace")
        return ParseResult(
            source_id, "stdlib-html-v1", tuple(normalize_html(source_id, text))
        )
    if suffix == ".pdf":
        return _parse_pdf_optional(source, source_id)
    if suffix == ".docx":
        return _parse_docx_optional(source, source_id)
    message = f"unsupported document format: {suffix or '<none>'}"
    raise ValueError(message)


@runtime_checkable
class PdfBackend(Protocol):
    """Optional PyMuPDF module surface; outputs remain untrusted objects."""

    def open(self, path: Path) -> object:
        """Open an original PDF for bounded text projection.

        Returns:
            The result described above, retaining the declared return-type contract.

        """
        ...


@runtime_checkable
class PdfReaderBackend(Protocol):
    """Optional pypdf factory without importing the dependency on the core path."""

    PdfReader: Callable[[str], object]


@runtime_checkable
class PdfReaderPort(Protocol):
    """External reader with untrusted pages."""

    pages: object


@runtime_checkable
class PdfTextPage(Protocol):
    """PyMuPDF page text method."""

    def get_text(self, mode: str) -> object:
        """Return extracted text for independent string validation.

        Returns:
            The result described above, retaining the declared return-type contract.

        """
        ...


@runtime_checkable
class PdfPage(Protocol):
    """pypdf page text method."""

    def extract_text(self) -> object:
        """Return text or null; other types are rejected.

        Returns:
            The result described above, retaining the declared return-type contract.

        """
        ...


@runtime_checkable
class DocxBackend(Protocol):
    """Optional python-docx factory."""

    Document: Callable[[Path], object]


@runtime_checkable
class DocxPort(Protocol):
    """Untrusted document paragraph sequence."""

    paragraphs: object


@runtime_checkable
class ParagraphPort(Protocol):
    """Untrusted paragraph text."""

    text: object


@runtime_checkable
class ClosablePort(Protocol):
    """Release parser resources when supported by the backend."""

    def close(self) -> None:
        """Close the original input resource."""
        ...


def require_interface[T](value: object, expected: type[T]) -> T:
    """Check an external object against the required runtime interface before use.

    Returns:
        The same object after a successful runtime interface check.

    Raises:
        TypeError: An input or external return value has an incompatible concrete
        type.

    """
    if not isinstance(value, expected):
        message = "optional parser returned an incompatible interface"
        raise TypeError(message)
    return value


def _items(value: object) -> Iterable[object]:
    if not isinstance(value, Iterable):
        message = "optional parser must return iterable pages or paragraphs"
        raise TypeError(message)
    return cast("Iterable[object]", value)


def _parse_pypdf(path: Path, source_id: str) -> ParseResult:
    try:
        backend = require_interface(importlib.import_module("pypdf"), PdfReaderBackend)
    except ImportError as exc:
        message = "PDF parsing requires a qualified optional parser: pymupdf or pypdf"
        raise RuntimeError(message) from exc
    reader = require_interface(backend.PdfReader(str(path)), PdfReaderPort)
    segments: list[SilverSegment] = []
    for page_number, page in enumerate(_items(reader.pages), 1):
        text = optional_string(require_interface(page, PdfPage).extract_text()) or ""
        segments.extend(
            normalize_text(f"{source_id}.p{page_number}", text, parser_id="pypdf-v1")
        )
    return ParseResult(source_id, "pypdf-v1", tuple(segments))


def _parse_pdf_optional(path: Path, source_id: str) -> ParseResult:
    try:
        backend = require_interface(importlib.import_module("pymupdf"), PdfBackend)
    except ImportError:
        return _parse_pypdf(path, source_id)
    document = backend.open(path)
    segments: list[SilverSegment] = []
    try:
        for page_number, page in enumerate(_items(document), 1):
            text = string(require_interface(page, PdfTextPage).get_text("text"))
            segments.extend(
                normalize_text(
                    f"{source_id}.p{page_number}", text, parser_id="pymupdf-v1"
                )
            )
    finally:
        if isinstance(document, ClosablePort):
            document.close()
    return ParseResult(source_id, "pymupdf-v1", tuple(segments))


def _parse_docx_optional(path: Path, source_id: str) -> ParseResult:
    try:
        backend = require_interface(importlib.import_module("docx"), DocxBackend)
    except ImportError as exc:
        message = "DOCX parsing requires the qualified optional parser python-docx"
        raise RuntimeError(message) from exc
    document = require_interface(backend.Document(path), DocxPort)
    text = "\n".join(
        string(require_interface(paragraph, ParagraphPort).text)
        for paragraph in _items(document.paragraphs)
    )
    warnings = ("docx_tables_not_extracted",) if getattr(document, "tables", ()) else ()
    return ParseResult(
        source_id,
        "python-docx-v1",
        tuple(normalize_text(source_id, text, parser_id="python-docx-v1")),
        warnings,
    )
