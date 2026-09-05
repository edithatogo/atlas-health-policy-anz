"""Malformed adapter values fail before they can become accepted evidence."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

import sys
import types
from dataclasses import dataclass, field, replace
from typing import Never, Self

import pytest

from australian_health_policy_atlas import capture
from australian_health_policy_atlas.parsers import (
    PdfBackend,
    parse_file,
    require_interface,
)
from tests.support import ignoring_arguments


@dataclass
class Response:
    body: object = b"original"
    headers: object = field(default_factory=lambda: {"Content-Type": "text/plain"})
    status: object = 200
    url: object = "https://health.test/policy"
    closed: bool = False

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.closed = True

    def read(self, _amount: int) -> object:
        return self.body

    def geturl(self) -> object:
        return self.url


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"body": "not bytes"}, "HTTP response body must be bytes"),
        ({"headers": []}, "HTTP headers must expose a mapping"),
        ({"status": True}, "integer required"),
        ({"url": 123}, "string required"),
    ],
)
def test_invalid_http_fields_are_closed_and_not_retried(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    changes: dict[str, object],
    message: str,
) -> None:
    response = replace(Response(), **changes)
    monkeypatch.setattr(capture, "urlopen", ignoring_arguments(lambda: response))

    def reject_sleep(_seconds: float) -> Never:
        error = "Type errors must not be retried"
        raise AssertionError(error)

    monkeypatch.setattr(capture.time, "sleep", reject_sleep)
    with pytest.raises(TypeError, match=message):
        capture.capture_url("https://health.test/policy", cas_root=tmp_path, retries=3)
    assert response.closed


def test_non_context_managed_http_response_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(capture, "urlopen", ignoring_arguments(object))
    with pytest.raises(TypeError, match="context-managed closure"):
        capture.capture_url("https://health.test/policy", cas_root=tmp_path)


def test_optional_parser_interface_is_checked() -> None:
    with pytest.raises(TypeError, match="incompatible interface"):
        require_interface(object(), PdfBackend)


@pytest.mark.parametrize("contents", [None, "not a page", 123])
def test_malformed_pdf_pages_still_close_the_reader(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, contents: object
) -> None:
    class Document:
        closed = False

        def __iter__(self) -> Iterator[object]:
            yield contents

        def close(self) -> None:
            self.closed = True

    document = Document()
    module = types.ModuleType("pymupdf")
    monkeypatch.setattr(
        module, "open", ignoring_arguments(lambda: document), raising=False
    )
    monkeypatch.setitem(sys.modules, "pymupdf", module)
    path = tmp_path / "synthetic.pdf"
    path.write_bytes(b"fixture only, not a PDF")
    with pytest.raises(TypeError, match="incompatible interface"):
        parse_file(path, source_id="fixture")
    assert document.closed


def test_non_iterable_pdf_page_collection_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = types.ModuleType("pymupdf")
    monkeypatch.setattr(module, "open", ignoring_arguments(lambda: 123), raising=False)
    monkeypatch.setitem(sys.modules, "pymupdf", module)
    path = tmp_path / "synthetic.pdf"
    path.write_bytes(b"fixture only, not a PDF")
    with pytest.raises(TypeError, match="iterable pages or paragraphs"):
        parse_file(path, source_id="fixture")
