import pytest

from australian_health_policy_atlas.external_tools import run_json_tool


def test_empty_external_command_rejected() -> None:
    with pytest.raises(ValueError, match="explicit"):
        run_json_tool("x", [], {})
