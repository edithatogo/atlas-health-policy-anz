"""Bounded HTTPS acquisition with content-addressed receipts."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from http.client import HTTPMessage


import ipaddress
import socket
import time
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import UTC, datetime
from email.message import Message
from pathlib import Path
from typing import (
    IO,
    Protocol,
    TypedDict,
    Unpack,
    cast,
    override,
    runtime_checkable,
)
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .hashing import sha256_bytes, sha256_json
from .integrity import atomic_bytes, atomic_json
from .records import integer, optional_string, string

FIRST_VISIBLE_ASCII = 33
SERVER_ERROR_START = 500


@dataclass(frozen=True, slots=True)
class CaptureReceipt:
    """Observed HTTP context and the independently hashed original response body."""

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
        """Return this typed record as a serialization-ready dictionary.

        Returns:
            A dictionary containing this record's declared fields.

        """
        return {
            "requested_url": self.requested_url,
            "final_url": self.final_url,
            "http_status": self.http_status,
            "observed_at": self.observed_at,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "media_type": self.media_type,
            "etag": self.etag,
            "last_modified": self.last_modified,
            "stored_path": self.stored_path,
        }


class CapturePort(Protocol):
    """Minimal capture interface used by finite crawl orchestration."""

    def __call__(
        self,
        url: str,
        *,
        cas_root: Path,
        max_bytes: int,
        retries: int,
        allowed_hosts: tuple[str, ...],
    ) -> CaptureReceipt:
        """Capture one explicitly bounded source URL with a verifiable receipt.

        Returns:
            The result described above, retaining the declared return-type contract.

        """
        ...


def validate_public_https(url: str) -> None:
    """Reject non-public, credential-bearing or unsafe HTTPS source URLs.

    Raises:
        ValueError: The supplied data violates the function's documented validation
        contract.

    """
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        message = "capture only permits explicit HTTPS URLs"
        raise ValueError(message)
    if parsed.username or parsed.password:
        message = "credentials must not be embedded in source URLs"
        raise ValueError(message)
    if parsed.port not in {None, 443} or any(ord(c) < FIRST_VISIBLE_ASCII for c in url):
        message = "unsafe HTTPS source URL"
        raise ValueError(message)
    host = parsed.hostname
    if host == "localhost" or host.endswith((".localhost", ".local", ".internal")):
        message = "non-public source host"
        raise ValueError(message)
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return
    if not address.is_global:
        message = "non-public source address"
        raise ValueError(message)


def resolve_public(url: str) -> None:
    """Resolve a validated source host and reject non-public address answers.

    Raises:
        ValueError: The supplied data violates the function's documented validation
        contract.

    """
    validate_public_https(url)
    host = urlparse(url).hostname
    answers = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    if not answers or any(not ipaddress.ip_address(a[4][0]).is_global for a in answers):
        message = "source DNS resolved to non-public address"
        raise ValueError(message)


def _validate_redirect_target(url: str, hosts: tuple[str, ...]) -> None:
    validate_public_https(url)
    if urlparse(url).hostname not in hosts:
        message = "redirect outside explicit source hosts"
        raise ValueError(message)
    resolve_public(url)


class SourceRedirect(HTTPRedirectHandler):
    """Redirect handler restricted to the declared public HTTPS source hosts."""

    def __init__(self, hosts: tuple[str, ...]) -> None:
        """Store the explicit source-host allowlist for redirect validation."""
        self.hosts = hosts

    @override
    def redirect_request(
        self,
        req: Request,
        fp: IO[bytes],
        code: int,
        msg: str,
        headers: HTTPMessage,
        newurl: str,
    ) -> Request | None:
        """Validate a redirect target before creating the follow-up HTTP request.

        Returns:
            A validated redirect request or None when the base handler declines it.

        Raises:
            OSError: Public-address resolution fails before the redirect is followed.
            ValueError: The supplied data violates the function's documented
            validation contract.

        """
        try:
            _validate_redirect_target(newurl, self.hosts)
        except ValueError, OSError:
            fp.close()
            raise
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class SourceRequest(Request):  # ruff: ignore[suspicious-url-open-usage] - HTTPS and explicit hosts validated before use.
    """Request with an explicit redirect allowlist, never an inferred credential."""

    atlas_allowed_hosts: tuple[str, ...] = ()


@runtime_checkable
class ResponsePort(Protocol):
    """Structural response boundary; every returned field is untrusted."""

    headers: object
    status: object

    def read(self, amount: int) -> object:
        """Read a bounded body whose concrete byte type is checked by the caller.

        Returns:
            The result described above, retaining the declared return-type contract.

        """
        ...

    def geturl(self) -> object:
        """Return the observed URL for independent boundary validation.

        Returns:
            The result described above, retaining the declared return-type contract.

        """
        ...


@runtime_checkable
class HeaderPort(Protocol):
    """Mapping-like header boundary with untrusted field values."""

    def get(self, name: str, default: object = None) -> object:
        """Download pinned public bytes anonymously for verification.

        Returns:
            The bytes returned by an anonymous exact-revision download.

        """
        ...


class CaptureOptions(TypedDict, total=False):
    """Precisely typed optional acquisition settings retained by the public API."""

    receipt_path: str | Path | None
    max_bytes: int
    timeout_seconds: int
    retries: int
    allowed_hosts: tuple[str, ...] | None
    user_agent: str


def urlopen(request: Request, *, timeout: int) -> object:
    """Restrict DNS and redirects; return an untrusted external response object.

    Returns:
        The result described above, retaining the declared return-type contract.

    """
    resolve_public(request.full_url)
    hosts = (
        request.atlas_allowed_hosts
        if isinstance(request, SourceRequest)
        else (string(urlparse(request.full_url).hostname),)
    )
    return cast(
        "object", build_opener(SourceRedirect(hosts)).open(request, timeout=timeout)
    )


def _read_body(response: ResponsePort, max_bytes: int) -> bytes:
    data = response.read(max_bytes + 1)
    if not isinstance(data, bytes):
        message = "HTTP response body must be bytes"
        raise TypeError(message)
    if len(data) > max_bytes:
        message = f"source exceeds max_bytes={max_bytes}"
        raise ValueError(message)
    return data


def _response_headers(value: object) -> tuple[str, str | None, str | None]:
    if not isinstance(value, HeaderPort):
        message = "HTTP headers must expose a mapping interface"
        raise TypeError(message)
    media_type = (
        value.get_content_type()
        if isinstance(value, Message)
        else string(value.get("Content-Type", "application/octet-stream")).split(
            ";", 1
        )[0]
    )
    return (
        media_type,
        optional_string(value.get("ETag")),
        optional_string(value.get("Last-Modified")),
    )


def _make_receipt(
    url: str,
    response: object,
    cas_root: Path,
    hosts: tuple[str, ...],
    max_bytes: int,
) -> CaptureReceipt:
    if not isinstance(response, ResponsePort):
        message = "invalid HTTP response interface"
        raise TypeError(message)
    final_url = string(response.geturl())
    validate_public_https(final_url)
    if urlparse(final_url).hostname not in hosts:
        message = "final response outside source hosts"
        raise ValueError(message)
    data = _read_body(response, max_bytes)
    digest = sha256_bytes(data)
    target = cas_root / "sha256" / digest[:2] / digest
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        atomic_bytes(target, data)
    if sha256_bytes(target.read_bytes()) != digest:
        message = "CAS fixity verification failed"
        raise OSError(message)
    media_type, etag, last_modified = _response_headers(response.headers)
    return CaptureReceipt(
        requested_url=url,
        final_url=final_url,
        http_status=integer(response.status),
        observed_at=datetime.now(UTC).isoformat(),
        sha256=digest,
        size_bytes=len(data),
        media_type=media_type,
        etag=etag,
        last_modified=last_modified,
        stored_path=str(target),
    )


def _capture_once(
    url: str,
    cas_root: Path,
    hosts: tuple[str, ...],
    options: CaptureOptions,
) -> CaptureReceipt:
    request = SourceRequest(
        url,
        headers={
            "User-Agent": options.get(
                "user_agent",
                "AustralianHealthPolicyAtlas/0.1 (+public-policy-research)",
            ),
            "Accept": "*/*",
        },
    )
    request.atlas_allowed_hosts = hosts
    raw = urlopen(request, timeout=options.get("timeout_seconds", 60))
    if not isinstance(raw, AbstractContextManager):
        message = "HTTP response must support context-managed closure"
        raise TypeError(message)
    with cast("AbstractContextManager[object]", raw) as response:
        receipt = _make_receipt(
            url, response, cas_root, hosts, options.get("max_bytes", 128 * 1024 * 1024)
        )
    path = options.get("receipt_path")
    if path is not None:
        payload = receipt.as_dict()
        payload["receipt_sha256"] = sha256_json(payload)
        atomic_json(Path(path), payload)
    return receipt


def _retryable(exc: Exception) -> bool:
    if isinstance(exc, (TypeError, ValueError)):
        return False
    if isinstance(exc, HTTPError):
        exc.close()
        return exc.code in {408, 425, 429} or exc.code >= SERVER_ERROR_START
    return True


def capture_url(
    url: str, *, cas_root: str | Path, **options: Unpack[CaptureOptions]
) -> CaptureReceipt:
    """Acquire original bytes within explicit host, size and retry boundaries.

    Returns:
        The result described above, retaining the declared return-type contract.

    Raises:
        ValueError: Source scope, identity or resource-budget validation fails.
        RuntimeError: The bounded operation cannot produce a valid terminal result.

    """
    validate_public_https(url)
    hosts = options.get("allowed_hosts") or (string(urlparse(url).hostname),)
    if urlparse(url).hostname not in hosts:
        message = "requested URL outside source hosts"
        raise ValueError(message)
    max_bytes, retries = (
        options.get("max_bytes", 128 * 1024 * 1024),
        options.get("retries", 2),
    )
    if (
        type(max_bytes) is not int
        or max_bytes <= 0
        or type(retries) is not int
        or retries < 0
        or options.get("timeout_seconds", 60) <= 0
    ):
        message = "invalid acquisition budget"
        raise ValueError(message)
    for attempt in range(retries + 1):
        try:
            return _capture_once(url, Path(cas_root), hosts, options)
        except Exception as exc:
            if not _retryable(exc) or attempt == retries:
                raise
            time.sleep(min(1 << attempt, 4))
    message = "validated retry budget unexpectedly exhausted"
    raise RuntimeError(message)
