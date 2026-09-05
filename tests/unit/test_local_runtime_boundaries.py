"""Untrusted model responses cannot escape loopback or bypass output validation."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytest_httpserver import HTTPServer

import json

import pytest

from australian_health_policy_atlas.microtasks import EvidenceInput, compile_packet
from australian_health_policy_atlas.runtime import llamacpp as runtime
from tests.support import ignoring_arguments
from tests.unit.test_external_response_boundaries import Response


def _packet() -> dict[str, object]:
    return compile_packet(
        task_id="fixture",
        skill_id="modality",
        objective="Classify modality",
        open_question="Is the supplied clause mandatory?",
        evidence=[EvidenceInput("fixture", "span", "Nurses must document care.")],
        output_schema={
            "type": "object",
            "additionalProperties": False,
            "required": ["modality", "source_span_id"],
            "properties": {
                "modality": {"enum": ["must"]},
                "source_span_id": {"type": "string"},
            },
        },
        invariants=["Use the exact supplied span only."],
        stop_conditions=["Return one schema-valid result or abstain."],
        abstention_codes=["ambiguous_modality"],
    )


@pytest.mark.parametrize(
    "endpoint",
    [
        "file://localhost/etc/passwd",
        "ftp://127.0.0.1/model",
        "http://user:secret@localhost/model",
        "http://localhost/model#fragment",
        "http://localhost:0/model",
        "http://localhost:65536/model",
        "http://localhost/mo\ndel",
    ],
)
def test_local_host_alone_is_not_a_safe_endpoint(endpoint: str) -> None:
    with pytest.raises(ValueError, match=r"HTTP\(S\)|endpoint port|Port out of range"):
        runtime.require_loopback(endpoint)


@pytest.mark.parametrize("timeout", [0, -1, True])
def test_runtime_timeout_is_bounded(timeout: int) -> None:
    with pytest.raises(ValueError, match="positive integer runtime timeout"):
        runtime.invoke_openai_compatible(_packet(), timeout_seconds=timeout)


@pytest.mark.parametrize(
    ("response", "error", "message"),
    [
        (object(), TypeError, "context-managed closure"),
        (Response(body="not bytes"), TypeError, "runtime response must be bytes"),
        (
            Response(body=b"x" * (runtime.MAX_RESPONSE_BYTES + 1)),
            ValueError,
            "bounded output limit",
        ),
        (Response(body=b'{"choices":[]}'), ValueError, "exactly one completion"),
        (Response(body=b'{"choices":[{},{}]}'), ValueError, "exactly one completion"),
        (Response(body=b'{"choices":1e309}'), ValueError, "non-finite JSON number"),
    ],
)
def test_malformed_runtime_responses_are_rejected(
    monkeypatch: pytest.MonkeyPatch,
    response: object,
    error: type[Exception],
    message: str,
) -> None:
    monkeypatch.setattr(runtime, "urlopen", ignoring_arguments(lambda: response))
    with pytest.raises(error, match=message):
        runtime.invoke_openai_compatible(_packet())
    if isinstance(response, Response):
        assert response.closed


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_native_loopback_transport_ignores_external_proxy_settings(
    httpserver: HTTPServer, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("http_proxy", "http://203.0.113.1:9")
    monkeypatch.setenv("https_proxy", "http://203.0.113.1:9")
    monkeypatch.setenv("no_proxy", "")
    monkeypatch.setenv("NO_PROXY", "")
    output = {"modality": "must", "source_span_id": "span"}
    httpserver.expect_request("/model", method="POST").respond_with_json({
        "choices": [{"message": {"content": json.dumps(output)}}]
    })
    result = runtime.invoke_openai_compatible(
        _packet(), endpoint=httpserver.url_for("/model")
    )
    assert result.output == output


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_native_loopback_redirect_is_rejected_before_follow_up(
    httpserver: HTTPServer,
) -> None:
    httpserver.expect_request("/redirect", method="POST").respond_with_data(
        b"", status=302, headers={"Location": "https://example.invalid/collect"}
    )
    with pytest.raises(ValueError, match="redirects are not permitted"):
        runtime.invoke_openai_compatible(
            _packet(), endpoint=httpserver.url_for("/redirect")
        )
