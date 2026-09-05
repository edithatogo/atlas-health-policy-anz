"""Dependency-free Silver normalisation for HTML/text; richer parsers plug in later."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable


import html
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import override

from .hashing import sha256_text


@dataclass(frozen=True, slots=True)
class SilverSegment:
    """Normalised source segment retaining its text hash and source identity."""

    segment_id: str
    source_id: str
    ordinal: int
    text: str
    text_sha256: str
    locator: str
    parser_id: str

    def as_dict(self) -> dict[str, object]:
        """Return the record without losing its declared field types.

        Returns:
            A dictionary containing this record's declared fields.

        """
        return {
            "segment_id": self.segment_id,
            "source_id": self.source_id,
            "ordinal": self.ordinal,
            "text": self.text,
            "text_sha256": self.text_sha256,
            "locator": self.locator,
            "parser_id": self.parser_id,
        }


class _VisibleTextParser(HTMLParser):
    BLOCKS = frozenset({
        "p",
        "li",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "td",
        "th",
        "blockquote",
    })

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._buffer: list[str] = []
        self.blocks: list[str] = []
        self._ignore_depth = 0

    @override
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self._ignore_depth += 1
        if tag in self.BLOCKS and self._buffer:
            self._flush()

    @override
    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._ignore_depth:
            self._ignore_depth -= 1
        if tag in self.BLOCKS:
            self._flush()

    @override
    def handle_data(self, data: str) -> None:
        if not self._ignore_depth:
            self._buffer.append(data)

    @override
    def close(self) -> None:
        super().close()
        self._flush()

    def _flush(self) -> None:
        text = re.sub(r"\s+", " ", html.unescape(" ".join(self._buffer))).strip()
        self._buffer.clear()
        if text:
            self.blocks.append(text)


def normalize_text(
    source_id: str, text: str, *, parser_id: str = "plain-text-v1"
) -> list[SilverSegment]:
    """Create deterministic text segments and hash-bound source anchors.

    Returns:
        Hash-bound segments in source-text order.

    """
    blocks = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    blocks = [item for item in blocks if item]
    return _segments(source_id, blocks, parser_id)


def normalize_html(
    source_id: str, html_text: str, *, parser_id: str = "stdlib-html-v1"
) -> list[SilverSegment]:
    """Project HTML text into deterministic segments without executing page content.

    Returns:
        Normalised text segments in the parser-observed document order.

    """
    parser = _VisibleTextParser()
    parser.feed(html_text)
    parser.close()
    return _segments(source_id, parser.blocks, parser_id)


def _segments(
    source_id: str, blocks: Iterable[str], parser_id: str
) -> list[SilverSegment]:
    output: list[SilverSegment] = []
    for index, text in enumerate(blocks, 1):
        digest = sha256_text(text)
        output.append(
            SilverSegment(
                segment_id=f"{source_id}.seg.{index:06d}",
                source_id=source_id,
                ordinal=index,
                text=text,
                text_sha256=digest,
                locator=f"segment:{index}",
                parser_id=parser_id,
            )
        )
    return output
