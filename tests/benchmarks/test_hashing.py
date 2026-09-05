"""Record CPU throughput without interpreting shared-runner timing as correctness."""

import hashlib
from typing import TYPE_CHECKING

import pytest

from australian_health_policy_atlas.hashing import sha256_bytes

if TYPE_CHECKING:
    from pytest_benchmark.fixture import BenchmarkFixture


@pytest.mark.benchmark
def test_hash_throughput(benchmark: BenchmarkFixture) -> None:
    payload = b"policy-integrity-fixture" * 1024
    result = benchmark(sha256_bytes, payload)
    assert result == hashlib.sha256(payload).hexdigest()
