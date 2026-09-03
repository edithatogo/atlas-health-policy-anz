"""Bounded HTTPS acquisition with content-addressed receipts."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .hashing import sha256_bytes, sha256_json


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


def capture_url(
    url: str,
    *,
    cas_root: str | Path,
    receipt_path: str | Path | None = None,
    max_bytes: int = 128 * 1024 * 1024,
    timeout_seconds: int = 60,
    retries: int = 2,
    user_agent: str = "AustralianHealthPolicyAtlas/0.1 (+public-policy-research)",
) -> CaptureReceipt:
    _validate_public_https(url)
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            request = Request(url, headers={"User-Agent": user_agent, "Accept": "*/*"})
            with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 - URL validated as HTTPS
                data = response.read(max_bytes + 1)
                if len(data) > max_bytes:
                    raise ValueError(f"source exceeds max_bytes={max_bytes}")
                digest = sha256_bytes(data)
                target = Path(cas_root) / "sha256" / digest[:2] / digest
                target.parent.mkdir(parents=True, exist_ok=True)
                if not target.exists():
                    target.write_bytes(data)
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
                    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                return receipt
        except Exception as exc:  # noqa: BLE001 - errors are preserved and bounded for retries
            last_error = exc
            if attempt < retries:
                time.sleep(min(2**attempt, 4))
    assert last_error is not None
    raise last_error
