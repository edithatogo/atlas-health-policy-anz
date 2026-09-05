"""Deterministic link discovery from captured policy portal HTML."""

from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import urldefrag, urljoin, urlparse


@dataclass(frozen=True, slots=True)
class DiscoveredLink:
    url: str
    anchor_text: str
    likely_document: bool
    extension: str


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._href is not None:
            self.links.append((self._href, " ".join(self._text).strip()))
            self._href = None
            self._text = []


def discover_links(
    html_text: str,
    *,
    base_url: str,
    same_host_only: bool = True,
    document_extensions: tuple[str, ...] = (
        ".pdf",
        ".doc",
        ".docx",
        ".rtf",
        ".odt",
        ".html",
        ".htm",
    ),
) -> list[DiscoveredLink]:
    parser = _LinkParser()
    parser.feed(html_text)
    base_host = urlparse(base_url).hostname
    seen: set[str] = set()
    output: list[DiscoveredLink] = []
    for href, text in parser.links:
        absolute, _fragment = urldefrag(urljoin(base_url, href))
        parsed = urlparse(absolute)
        if parsed.scheme not in {"http", "https"}:
            continue
        if same_host_only and parsed.hostname != base_host:
            continue
        if absolute in seen:
            continue
        seen.add(absolute)
        path_lower = parsed.path.lower()
        extension = next(
            (ext for ext in document_extensions if path_lower.endswith(ext)), ""
        )
        document_words = (
            "policy",
            "guideline",
            "procedure",
            "directive",
            "standard",
            "framework",
            "manual",
        )
        likely = bool(extension) or any(
            word in (text + " " + parsed.path).lower() for word in document_words
        )
        output.append(DiscoveredLink(absolute, text, likely, extension))
    return output
