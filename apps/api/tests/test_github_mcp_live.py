"""Opt-in actual official-server read. Never substitute the local protocol tests."""

import os

import anyio
import pytest

from repopilot.config import Settings
from repopilot.github.client import GitHubMCPError
from repopilot.github.probe import probe

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_GITHUB_MCP_TESTS") != "1",
    reason="requires explicit opt-in and locally configured GitHub MCP credential",
)


def test_actual_official_github_mcp_discovery_and_identity():
    try:
        report = anyio.run(probe, Settings(), "juice-gift")
    except GitHubMCPError as exc:
        pytest.fail("Actual GitHub MCP check failed: " + exc.code, pytrace=False)
    assert report["status"] == "passed"
    assert report["identity_matches_expected"]
    assert report["readonly"]
    assert report["remote_writes"] == 0
