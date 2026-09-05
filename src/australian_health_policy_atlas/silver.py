"""Dependency-free Silver normalisation for HTML/text; richer parsers plug in later."""

from __future__ import annotations

import html
import re
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from typing import Iterable

from .hashing import sha256_text


@dataclass(frozen=True, slots=True)
class SilverSegment:
    segment_id: str
    source_id: str
    ordinal: int
    text: str
    text_sha256: str
    locator: str
    parser_id: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


class _VisibleTextParser(HTMLParser):
    BLOCKS = frozenset({"p", "li", "h1", "h2", "h3", "h4", "h5", "h6", "td", "th", "blockquote"})

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._buffer: list[str] = []
        self.blocks: list[str] = []
        self._ignore_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self._ignore_depth += 1
        if tag in self.BLOCKS and self._buffer:
            self._flush()

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._ignore_depth:
            self._ignore_depth -= 1
        if tag in self.BLOCKS:
            self._flush()

    def handle_data(self, data: str) -> None:
        if not self._ignore_depth:
            self._buffer.append(data)

    def close(self) -> None:
        super().close()
        self._flush()

    def _flush(self) -> None:
        text = re.sub(r"\s+", " ", html.unescape(" ".join(self._buffer))).strip()
        self._buffer.clear()
        if text:
            self.blocks.append(text)


def normalize_text(source_id: str, text: str, *, parser_id: str = "plain-text-v1") -> list[SilverSegment]:
    blocks = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    blocks = [item for item in blocks if item]
    return _segments(source_id, blocks, parser_id)


def normalize_html(source_id: str, html_text: str, *, parser_id: str = "stdlib-html-v1") -> list[SilverSegment]:
    parser = _VisibleTextParser()
    parser.feed(html_text)
    parser.close()
    return _segments(source_id, parser.blocks, parser_id)


def _segments(source_id: str, blocks: Iterable[str], parser_id: str) -> list[SilverSegment]:
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
