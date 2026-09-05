"""Bounded HTTPS acquisition with content-addressed receipts."""

from __future__ import annotations

import ipaddress
import socket
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .hashing import sha256_bytes, sha256_json
from .integrity import atomic_bytes, atomic_json


@dataclass(frozen=True, slots=True)
class CaptureReceipt:
    requested_url: str
    final_url: str
    http_status: int
    observed_at: str
    sha256: str
    size_bytes: int
    media_type: str
    etag: str | None
    last_modified: str | None
    stored_path: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _validate_public_https(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("capture only permits explicit HTTPS URLs")
    if parsed.username or parsed.password:
        raise ValueError("credentials must not be embedded in source URLs")
    if parsed.port not in (None, 443) or any(ord(c) < 33 for c in url):
        raise ValueError("unsafe HTTPS source URL")
    host = parsed.hostname
    if host == "localhost" or host.endswith((".localhost", ".local", ".internal")):
        raise ValueError("non-public source host")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return
    if not address.is_global:
        raise ValueError("non-public source address")


def _resolve_public(url: str) -> None:
    _validate_public_https(url)
    host = urlparse(url).hostname
    answers = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    if not answers or any(not ipaddress.ip_address(a[4][0]).is_global for a in answers):
        raise ValueError("source DNS resolved to non-public address")


class _SourceRedirect(HTTPRedirectHandler):
    def __init__(self, hosts: tuple[str, ...]) -> None:
        self.hosts = hosts

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _validate_public_https(newurl)
        if urlparse(newurl).hostname not in self.hosts:
            raise ValueError("redirect outside explicit source hosts")
        _resolve_public(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def urlopen(request: Request, *, timeout: int):
    """Restricted urllib boundary; DNS checking does not replace deployment egress rules."""
    _resolve_public(request.full_url)
    hosts = getattr(request, "atlas_allowed_hosts", (urlparse(request.full_url).hostname,))
    return build_opener(_SourceRedirect(hosts)).open(request, timeout=timeout)


def capture_url(
    url: str,
    *,
    cas_root: str | Path,
    receipt_path: str | Path | None = None,
    max_bytes: int = 128 * 1024 * 1024,
    timeout_seconds: int = 60,
    retries: int = 2,
    allowed_hosts: tuple[str, ...] | None = None,
    user_agent: str = "AustralianHealthPolicyAtlas/0.1 (+public-policy-research)",
) -> CaptureReceipt:
    _validate_public_https(url)
    hosts = allowed_hosts or (urlparse(url).hostname,)
    if urlparse(url).hostname not in hosts:
        raise ValueError("requested URL outside source hosts")
    if type(max_bytes) is not int or max_bytes <= 0 or type(retries) is not int or retries < 0 or timeout_seconds <= 0:
        raise ValueError("invalid acquisition budget")
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            request = Request(url, headers={"User-Agent": user_agent, "Accept": "*/*"})
            request.atlas_allowed_hosts = hosts
            with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 - URL validated as HTTPS
                _validate_public_https(response.geturl())
                if urlparse(response.geturl()).hostname not in hosts:
                    raise ValueError("final response outside source hosts")
                data = response.read(max_bytes + 1)
                if len(data) > max_bytes:
                    raise ValueError(f"source exceeds max_bytes={max_bytes}")
                digest = sha256_bytes(data)
                target = Path(cas_root) / "sha256" / digest[:2] / digest
                target.parent.mkdir(parents=True, exist_ok=True)
                if not target.exists():
                    atomic_bytes(target, data)
                if sha256_bytes(target.read_bytes()) != digest:
                    raise OSError("CAS fixity verification failed")
                headers = response.headers
                media_type = headers.get_content_type() if hasattr(headers, "get_content_type") else headers.get("Content-Type", "application/octet-stream").split(";", 1)[0]
                receipt = CaptureReceipt(
                    requested_url=url,
                    final_url=response.geturl(),
                    http_status=int(getattr(response, "status", 200)),
                    observed_at=datetime.now(UTC).isoformat(),
                    sha256=digest,
                    size_bytes=len(data),
                    media_type=media_type,
                    etag=headers.get("ETag"),
                    last_modified=headers.get("Last-Modified"),
                    stored_path=str(target),
                )
                if receipt_path is not None:
                    path = Path(receipt_path)
                    path.parent.mkdir(parents=True, exist_ok=True)
                    payload = receipt.as_dict()
                    payload["receipt_sha256"] = sha256_json(payload)
                    atomic_json(path, payload)
                return receipt
        except Exception as exc:  # noqa: BLE001 - errors are preserved and bounded for retries
            last_error = exc
            if isinstance(exc, ValueError):
                raise
            if isinstance(exc, HTTPError) and exc.code not in {408, 425, 429} and exc.code < 500:
                raise
            if attempt < retries:
                time.sleep(min(2**attempt, 4))
    assert last_error is not None
    raise last_error
