import pytest

from australian_health_policy_atlas.runtime.llamacpp import _require_loopback


def test_runtime_rejects_non_loopback_endpoint() -> None:
    with pytest.raises(ValueError):
        _require_loopback("https://example.com/v1/chat/completions")


def test_runtime_allows_localhost() -> None:
    _require_loopback("http://127.0.0.1:8080/v1/chat/completions")
