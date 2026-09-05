from __future__ import annotations

from email.message import Message
from pathlib import Path
from typing import Self

import pytest

from australian_health_policy_atlas import capture
from tests.support import ignoring_arguments


class FakeResponse:
    def __init__(
        self,
        data: bytes = b"abc",
        url: str = "https://health.test/final",
        status: int = 200,
    ) -> None:
        self._data = data
        self._url = url
        self.status = status
        self.headers = Message()
        self.headers["Content-Type"] = "text/html; charset=utf-8"
        self.headers["ETag"] = '"x"'
        self.headers["Last-Modified"] = "Mon, 01 Jan 2026 00:00:00 GMT"

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self, _size: int) -> bytes:
        return self._data

    def geturl(self) -> str:
        return self._url


def test_capture_url_writes_cas_and_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(capture, "urlopen", ignoring_arguments(FakeResponse))
    receipt = capture.capture_url(
        "https://health.test/policy",
        cas_root=tmp_path / "cas",
        receipt_path=tmp_path / "receipt.json",
        retries=0,
    )
    assert receipt.http_status == 200
    assert receipt.media_type == "text/html"
    assert Path(receipt.stored_path).read_bytes() == b"abc"
    assert (tmp_path / "receipt.json").exists()


def test_capture_rejects_non_https_and_credentials(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="HTTPS"):
        capture.capture_url("http://health.test/x", cas_root=tmp_path)
    with pytest.raises(ValueError, match="credentials"):
        capture.capture_url("https://user:pass@health.test/x", cas_root=tmp_path)


def test_capture_rejects_oversized_payload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        capture, "urlopen", ignoring_arguments(lambda: FakeResponse(b"abcd"))
    )
    with pytest.raises(ValueError, match="max_bytes"):
        capture.capture_url(
            "https://health.test/x", cas_root=tmp_path, max_bytes=3, retries=0
        )


def test_capture_retries_then_succeeds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    attempts = iter([OSError("temporary"), FakeResponse()])

    def fake(*_args: object, **_kwargs: object) -> FakeResponse:
        value = next(attempts)
        if isinstance(value, Exception):
            raise value
        return value

    monkeypatch.setattr(capture, "urlopen", fake)
    monkeypatch.setattr(capture.time, "sleep", ignoring_arguments(lambda: None))
    receipt = capture.capture_url("https://health.test/x", cas_root=tmp_path, retries=1)
    assert receipt.size_bytes == 3


def test_capture_raises_last_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        capture,
        "urlopen",
        ignoring_arguments(lambda: (_ for _ in ()).throw(OSError("dead"))),
    )
    with pytest.raises(OSError, match="dead"):
        capture.capture_url("https://health.test/x", cas_root=tmp_path, retries=0)
