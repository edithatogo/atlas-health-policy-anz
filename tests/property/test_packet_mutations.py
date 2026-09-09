"""Pure single-byte tampering checks; no new models or live network required."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from hypothesis import given
from hypothesis import strategies as st

from australian_health_policy_atlas.packet_ingestion import inspect_packet
from tests.packet_support import PDF, packet_fixture


@given(
    index=st.integers(min_value=0, max_value=len(PDF) - 1),
    mask=st.integers(min_value=1, max_value=255),
)
def test_any_single_byte_mutation_breaks_original_fixity(index: int, mask: int) -> None:
    with TemporaryDirectory() as root:
        fixture = packet_fixture(Path(root))
        altered = bytearray(PDF)
        altered[index] ^= mask
        (fixture.root / "originals/alpha.pdf").write_bytes(altered)
        with pytest.raises(ValueError, match="hash mismatch"):
            inspect_packet(fixture.root, fixture.spec)
