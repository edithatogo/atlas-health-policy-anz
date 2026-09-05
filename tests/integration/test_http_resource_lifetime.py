"""Regression checks for the response leaks revealed by warnings-as-errors."""

from __future__ import annotations

from email.message import Message
from io import BytesIO
from typing import TYPE_CHECKING
from urllib.error import HTTPError

import pytest

from australian_health_policy_atlas.capture import capture_url
from australian_health_policy_atlas.crawl import CrawlPolicy, run_crawl
from australian_health_policy_atlas.records import record

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_mock import MockerFixture


@pytest.mark.integration
@pytest.mark.parametrize("status", [404, 503])
def test_capture_closes_http_error_before_propagation(
    tmp_path: Path,
    mocker: MockerFixture,
    status: int,
) -> None:
    body = BytesIO(b"synthetic error response")
    error = HTTPError(
        "https://health.test/policies", status, "fixture", Message(), body
    )
    opener = mocker.patch(
        "australian_health_policy_atlas.capture.urlopen", side_effect=error
    )
    try:
        with pytest.raises(HTTPError) as observed:
            capture_url("https://health.test/policies", cas_root=tmp_path, retries=0)
        assert observed.value is error
        assert body.closed
        opener.assert_called_once()
    finally:
        error.close()


@pytest.mark.integration
@pytest.mark.parametrize(
    ("status", "disposition"), [(404, "unavailable"), (503, "retryable")]
)
def test_crawl_closes_error_from_injected_capture_boundary(
    tmp_path: Path,
    mocker: MockerFixture,
    status: int,
    disposition: str,
) -> None:
    body = BytesIO(b"synthetic adapter error")
    error = HTTPError(
        "https://health.test/policies", status, "fixture", Message(), body
    )
    fetch = mocker.Mock(side_effect=error)
    policy = CrawlPolicy(
        "quality-http",
        "QLD",
        "https://health.test/policies",
        ("health.test",),
        "2026-09-05",
    )
    try:
        result = run_crawl(policy, tmp_path, request_budget=1, fetch=fetch)
        assert body.closed
        assert record(result["counts"])[disposition] == 1
        assert result["gate_b_passed"] is False
        fetch.assert_called_once()
    finally:
        error.close()
