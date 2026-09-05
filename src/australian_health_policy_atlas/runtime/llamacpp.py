"""Loopback-only llama.cpp/OpenAI-compatible runtime adapter."""

from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from ..microtasks import render_prompt
from ..verification import verify_model_output


@dataclass(frozen=True, slots=True)
class RuntimeReceipt:
    endpoint: str
    model: str
    output: dict[str, object]
    raw_response: dict[str, object]


def _require_loopback(endpoint: str) -> None:
    host = urlparse(endpoint).hostname
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("local runtime adapter only permits loopback endpoints")


def invoke_openai_compatible(
    packet: dict[str, object],
    *,
    endpoint: str = "http://127.0.0.1:8080/v1/chat/completions",
    model: str = "local-model",
    timeout_seconds: int = 120,
) -> RuntimeReceipt:
    _require_loopback(endpoint)
    prompt = render_prompt(packet)  # type: ignore[arg-type]
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
    request = Request(
        endpoint,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 - loopback validated above
        raw = json.loads(response.read().decode("utf-8"))
    content = raw["choices"][0]["message"]["content"]
    output = json.loads(content) if isinstance(content, str) else content
    verify_model_output(packet, output)  # type: ignore[arg-type]
    return RuntimeReceipt(endpoint=endpoint, model=model, output=output, raw_response=raw)
