import pytest

from australian_health_policy_atlas.runtime.llamacpp import require_loopback


def test_runtime_rejects_non_loopback_endpoint() -> None:
    with pytest.raises(ValueError, match="only permits loopback"):
        require_loopback("https://example.com/v1/chat/completions")


def test_runtime_allows_localhost() -> None:
    require_loopback("http://127.0.0.1:8080/v1/chat/completions")
