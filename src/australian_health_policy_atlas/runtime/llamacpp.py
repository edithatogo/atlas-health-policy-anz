"""Loopback-only llama.cpp/OpenAI-compatible runtime adapter."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping
    from http.client import HTTPMessage
    from typing import IO


import json
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Protocol, cast, override, runtime_checkable
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from australian_health_policy_atlas.microtasks import render_prompt
from australian_health_policy_atlas.parsers import require_interface
from australian_health_policy_atlas.records import decode_json, record, records
from australian_health_policy_atlas.verification import verify_model_output


@runtime_checkable
class ContentResponse(Protocol):
    """Untrusted local inference response body interface."""

    def read(self, amount: int) -> object:
        """Return raw response bytes for independent decoding and validation.

        Returns:
            The result described above, retaining the declared return-type contract.

        """
        ...


@dataclass(frozen=True, slots=True)
class RuntimeReceipt:
    """Local inference result and the unmodified structured response for audit."""

    endpoint: str
    model: str
    output: dict[str, object]
    raw_response: dict[str, object]


def require_loopback(endpoint: str) -> None:
    """Reject inference endpoints outside the explicit local-host allowlist.

    Raises:
        ValueError: The supplied data violates the function's documented validation
        contract.

    """
    parsed = urlparse(endpoint)
    if (
        parsed.scheme not in {"http", "https"}
        or parsed.username
        or parsed.password
        or parsed.fragment
    ):
        message = "runtime requires HTTP(S) without credentials or fragments"
        raise ValueError(message)
    if parsed.port == 0 or any(ord(char) < FIRST_VISIBLE_ASCII for char in endpoint):
        message = "invalid runtime endpoint port or characters"
        raise ValueError(message)
    host = parsed.hostname
    if host not in {"127.0.0.1", "localhost", "::1"}:
        message = "local runtime adapter only permits loopback endpoints"
        raise ValueError(message)


MAX_RESPONSE_BYTES = 1024 * 1024
FIRST_VISIBLE_ASCII = 33


class RejectRuntimeRedirects(HTTPRedirectHandler):
    """Never redirect local inference requests, including to another local port."""

    @override
    def redirect_request(
        self,
        req: Request,
        fp: IO[bytes],
        code: int,
        msg: str,
        headers: HTTPMessage,
        newurl: str,
    ) -> None:
        """Reject redirection before a follow-up request can be sent.

        Raises:
            ValueError: Local inference does not permit redirects.

        """
        fp.close()
        message = "local inference redirects are not permitted"
        raise ValueError(message)


def urlopen(request: Request, *, timeout: int) -> object:
    """Open a validated loopback request without proxies or automatic redirects.

    Returns:
        The untrusted response, whose interface and bytes are checked by the caller.

    """
    require_loopback(request.full_url)
    opener = build_opener(ProxyHandler({}), RejectRuntimeRedirects())
    return cast("object", opener.open(request, timeout=timeout))


def invoke_openai_compatible(
    packet: Mapping[str, object],
    *,
    endpoint: str = "http://127.0.0.1:8080/v1/chat/completions",
    model: str = "local-model",
    timeout_seconds: int = 120,
) -> RuntimeReceipt:
    """Invoke a loopback model and validate its structured response.

    Returns:
        The verified model output and its retained structured runtime response.

    Raises:
        TypeError: An input or external return value has an incompatible concrete type.
        ValueError: The timeout, response size, completion count or output is invalid.

    """
    require_loopback(endpoint)
    if type(timeout_seconds) is not int or timeout_seconds <= 0:
        message = "positive integer runtime timeout required"
        raise ValueError(message)
    prompt = render_prompt(packet)
    body = {
        "model": model,
        "temperature": 0,
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "atlas_output",
                "strict": True,
                "schema": packet["output_schema"],
            },
        },
    }
    request = Request(  # ruff: ignore[suspicious-url-open-usage] - Explicit loopback host validated before construction.
        endpoint,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    raw_response = urlopen(request, timeout=timeout_seconds)
    if not isinstance(raw_response, AbstractContextManager):
        message = "runtime response must support context-managed closure"
        raise TypeError(message)
    with cast("AbstractContextManager[object]", raw_response) as response:
        body_bytes = require_interface(response, ContentResponse).read(
            MAX_RESPONSE_BYTES + 1
        )
        if not isinstance(body_bytes, bytes):
            message = "runtime response must be bytes"
            raise TypeError(message)
        if len(body_bytes) > MAX_RESPONSE_BYTES:
            message = "runtime response exceeds the bounded output limit"
            raise ValueError(message)
        raw = record(decode_json(body_bytes))
    choices = records(raw.get("choices"))
    if len(choices) != 1:
        message = "runtime must return exactly one completion choice"
        raise ValueError(message)
    content = record(choices[0].get("message")).get("content")
    output = record(decode_json(content) if isinstance(content, str) else content)
    verify_model_output(packet, output)
    return RuntimeReceipt(
        endpoint=endpoint, model=model, output=output, raw_response=raw
    )
