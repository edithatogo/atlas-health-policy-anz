from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pathlib

    from australian_health_policy_atlas.capture import CaptureOptions


from email.message import Message
from http.client import HTTPMessage
from io import BytesIO
from types import SimpleNamespace
from typing import Never, override
from urllib.error import HTTPError
from urllib.request import Request

import pytest

from australian_health_policy_atlas import capture
from tests.support import ignoring_arguments
from tests.unit.test_capture import FakeResponse


@pytest.mark.parametrize(
    "url",
    [
        "https://127.0.0.1/a",
        "https://[::1]/a",
        "https://localhost/a",
        "https://x.local/a",
        "https://x.internal/a",
        "https://health.test:8443/a",
        "https://health.test/a b",
    ],
)
def test_nonpublic_capture_url(url: str) -> None:
    with pytest.raises(ValueError, match=r"HTTPS|credentials|non-public|unsafe"):
        capture.validate_public_https(url)


def test_public_literal_accepted() -> None:
    capture.validate_public_https("https://8.8.8.8/a")


def test_dns_and_redirect_boundaries(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        capture.socket,
        "getaddrinfo",
        ignoring_arguments(lambda: [(2, 1, 6, "", ("127.0.0.1", 443))]),
    )
    with pytest.raises(ValueError, match="non-public"):
        capture.resolve_public("https://health.test/x")
    monkeypatch.setattr(
        capture.socket,
        "getaddrinfo",
        ignoring_arguments(lambda: [(2, 1, 6, "", ("8.8.8.8", 443))]),
    )
    capture.resolve_public("https://health.test/x")
    handler = capture.SourceRedirect(("health.test",))
    with pytest.raises(ValueError, match="redirect"):
        handler.redirect_request(
            Request("https://health.test/x"),
            BytesIO(),
            302,
            "",
            HTTPMessage(),
            "https://else.test/x",
        )
    req = handler.redirect_request(
        Request("https://health.test/x"),
        BytesIO(),
        302,
        "",
        HTTPMessage(),
        "https://health.test/final",
    )
    assert req is not None
    assert req.full_url == "https://health.test/final"
    monkeypatch.setattr(
        capture,
        "build_opener",
        ignoring_arguments(
            lambda: SimpleNamespace(open=ignoring_arguments(lambda: "opened"))
        ),
    )
    assert capture.urlopen(Request("https://health.test/x"), timeout=1) == "opened"


def test_permanent_http_errors_are_not_retried(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    calls: list[int] = []

    def error(*_a: object, **_kw: object) -> None:
        calls.append(1)
        message = "https://health.test/x"
        raise HTTPError(message, 404, "gone", Message(), None)

    monkeypatch.setattr(capture, "urlopen", error)
    with pytest.raises(HTTPError):
        capture.capture_url("https://health.test/x", cas_root=tmp_path, retries=5)
    assert len(calls) == 1


def test_final_redirect_guard_precedes_body_read(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    class Response(FakeResponse):
        @override
        def read(self, _size: int) -> Never:
            message = "body must not be read"
            raise AssertionError(message)

    monkeypatch.setattr(
        capture,
        "urlopen",
        ignoring_arguments(lambda: Response(url="https://wrong.test/x")),
    )
    with pytest.raises(ValueError, match="outside"):
        capture.capture_url("https://health.test/x", cas_root=tmp_path)


@pytest.mark.parametrize(
    "params", [{"max_bytes": 0}, {"retries": -1}, {"allowed_hosts": ("else.test",)}]
)
def test_invalid_capture_budgets(
    tmp_path: pathlib.Path, params: CaptureOptions
) -> None:
    with pytest.raises(
        ValueError, match=r"invalid acquisition budget|outside source hosts"
    ):
        capture.capture_url("https://health.test/x", cas_root=tmp_path, **params)
