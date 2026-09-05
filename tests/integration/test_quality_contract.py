"""Exercise installed testing adapters, network isolation and strict configuration."""

import socket
import subprocess  # noqa: S404 - CompletedProcess fixture only; execution is mocked
import sys
import tomllib
from pathlib import Path
from typing import TYPE_CHECKING, cast
from urllib.request import urlopen

import pytest
from inline_snapshot import snapshot
from pytest_socket import SocketBlockedError

from australian_health_policy_atlas.domain import MedallionLayer
from australian_health_policy_atlas.external_tools import run_json_tool
from australian_health_policy_atlas.state_machine import promotion_gate

if TYPE_CHECKING:
    from http.client import HTTPResponse

    from pytest_httpserver import HTTPServer
    from pytest_mock import MockerFixture

    from tests.quality_protocols import SubprocessFixture


@pytest.mark.quality
def test_strict_configuration_is_executable_contract() -> None:
    root = Path(__file__).resolve().parents[2]
    config = cast(
        "dict[str, object]",
        tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8")),
    )
    tool = cast("dict[str, dict[str, object]]", config["tool"])
    pytest_config = cast("dict[str, object]", tool["pytest"]["ini_options"])
    assert pytest_config["strict"] is True
    assert pytest_config["filterwarnings"] == ["error"]
    assert tool["basedpyright"]["typeCheckingMode"] == "strict"
    assert tool["basedpyright"]["failOnWarnings"] is True
    assert tool["basedpyright"]["reportExplicitAny"] == "error"
    assert cast("dict[str, str]", tool["ty"]["rules"])["all"] == "error"
    assert cast("dict[str, object]", tool["ruff"]["lint"])["select"] == ["ALL"]


@pytest.mark.quality
def test_undeclared_network_access_is_blocked() -> None:
    with (
        pytest.warns(UserWarning, match=r"A test tried to use socket\.socket"),
        pytest.raises(SocketBlockedError),
    ):
        socket.socket()


@pytest.mark.quality
def test_subprocess_adapter_uses_registered_fixture(fp: SubprocessFixture) -> None:
    command = [sys.executable, "--version"]
    fp.register(command, stdout="synthetic-tool-output\n")
    result = run_json_tool("test-fixture", command, {"synthetic": True})
    assert result.returncode == 0
    assert result.stdout == "synthetic-tool-output\n"
    assert fp.call_count(command) == 1


@pytest.mark.quality
def test_external_tool_contract_uses_autospec(mocker: MockerFixture) -> None:
    completed = subprocess.CompletedProcess(["fixture"], 0, stdout="{}", stderr="")
    patched = mocker.patch(
        "australian_health_policy_atlas.external_tools.subprocess.run",
        autospec=True,
        return_value=completed,
    )
    run_json_tool("fixture", ["fixture"], {}, timeout_seconds=2)
    assert patched.call_args.kwargs["timeout"] == 2
    assert patched.call_args.kwargs["check"] is False
    assert "shell" not in patched.call_args.kwargs


@pytest.mark.quality
@pytest.mark.allow_hosts(["127.0.0.1"])
def test_http_contract_uses_loopback_only(httpserver: HTTPServer) -> None:
    httpserver.expect_request("/manifest").respond_with_data(b"synthetic-capture")
    response = cast(
        "HTTPResponse",
        urlopen(httpserver.url_for("/manifest"), timeout=2),  # noqa: S310 - loopback server and pytest-socket host restriction
    )
    with response:
        assert response.read() == b"synthetic-capture"


@pytest.mark.quality
def test_inline_snapshot_freezes_rejection_reasons() -> None:
    decision = promotion_gate(
        MedallionLayer.SILVER, closed_layers=set(), acceptance_results={}
    )
    assert {
        "permitted": decision.permitted,
        "reasons": list(decision.reasons),
    } == snapshot({
        "permitted": False,
        "reasons": ["predecessor_release_not_closed", "acceptance_evidence_missing"],
    })
