from types import SimpleNamespace
from urllib.error import HTTPError
from urllib.request import Request

import pytest
from test_capture import FakeResponse

from australian_health_policy_atlas import capture


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
def test_nonpublic_capture_url(url):
    with pytest.raises(ValueError):
        capture._validate_public_https(url)


def test_public_literal_accepted():
    capture._validate_public_https("https://8.8.8.8/a")


def test_dns_and_redirect_boundaries(monkeypatch):
    monkeypatch.setattr(
        capture.socket,
        "getaddrinfo",
        lambda *_a, **_kw: [(2, 1, 6, "", ("127.0.0.1", 443))],
    )
    with pytest.raises(ValueError, match="non-public"):
        capture._resolve_public("https://health.test/x")
    monkeypatch.setattr(
        capture.socket,
        "getaddrinfo",
        lambda *_a, **_kw: [(2, 1, 6, "", ("8.8.8.8", 443))],
    )
    capture._resolve_public("https://health.test/x")
    handler = capture._SourceRedirect(("health.test",))
    with pytest.raises(ValueError, match="redirect"):
        handler.redirect_request(
            Request("https://health.test/x"), None, 302, "", {}, "https://else.test/x"
        )
    req = handler.redirect_request(
        Request("https://health.test/x"), None, 302, "", {}, "https://health.test/final"
    )
    assert req.full_url == "https://health.test/final"
    monkeypatch.setattr(
        capture,
        "build_opener",
        lambda *_a: SimpleNamespace(open=lambda *_a, **_kw: "opened"),
    )
    assert capture.urlopen(Request("https://health.test/x"), timeout=1) == "opened"


def test_permanent_http_errors_are_not_retried(monkeypatch, tmp_path):
    calls = []

    def error(*_a, **_kw):
        calls.append(1)
        raise HTTPError("https://health.test/x", 404, "gone", {}, None)

    monkeypatch.setattr(capture, "urlopen", error)
    with pytest.raises(HTTPError):
        capture.capture_url("https://health.test/x", cas_root=tmp_path, retries=5)
    assert len(calls) == 1


def test_final_redirect_guard_precedes_body_read(monkeypatch, tmp_path):
    class Response(FakeResponse):
        def read(self, _size):
            raise AssertionError("body must not be read")

    monkeypatch.setattr(
        capture, "urlopen", lambda *_a, **_kw: Response(url="https://wrong.test/x")
    )
    with pytest.raises(ValueError, match="outside"):
        capture.capture_url("https://health.test/x", cas_root=tmp_path)


@pytest.mark.parametrize(
    "params", [{"max_bytes": 0}, {"retries": -1}, {"allowed_hosts": ("else.test",)}]
)
def test_invalid_capture_budgets(tmp_path, params):
    with pytest.raises(ValueError):
        capture.capture_url("https://health.test/x", cas_root=tmp_path, **params)
