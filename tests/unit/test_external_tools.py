import sys

from australian_health_policy_atlas.external_tools import run_json_tool


def test_external_tool_receipt_is_explicit_and_no_shell() -> None:
    receipt = run_json_tool("echo-json", [sys.executable, "-c", "import sys; print(sys.stdin.read())"], {"a": 1})
    assert receipt.returncode == 0
    assert '"a": 1' in receipt.stdout
