"""Trusted fixed entrypoint. Check isolation before importing any fixture source."""

import json
import os
import pathlib
import sys


def isolation() -> dict[str, object]:
    status = dict(line.split(":", 1) for line in pathlib.Path("/proc/self/status").read_text().splitlines() if ":" in line)
    assert os.getuid() == 65534 and os.getgid() == 65534
    assert int(status["CapEff"].strip(), 16) == 0
    assert int(status["CapBnd"].strip(), 16) == 0
    assert status["NoNewPrivs"].strip() == "1" and status["Seccomp"].strip() == "2"
    assert pathlib.Path("/sys/fs/cgroup/memory.max").read_text().strip() == "268435456"
    assert pathlib.Path("/sys/fs/cgroup/pids.max").read_text().strip() == "64"
    assert pathlib.Path("/sys/fs/cgroup/cpu.max").read_text().strip() == "100000 100000"
    assert sorted(p.name for p in pathlib.Path("/sys/class/net").iterdir()) == ["lo"]
    for name in ("/workspace", "/validation", "/"):
        assert os.statvfs(name).f_flag & os.ST_RDONLY
    assert not pathlib.Path("/var/run/docker.sock").exists()
    assert not any(key in os.environ for key in ("OPENAI_API_KEY", "DASHSCOPE_API_KEY", "DATABASE_URL", "POSTGRES_PASSWORD", "GITHUB_TOKEN"))
    return {"uid": os.getuid(), "no_new_privileges": True, "seccomp": True, "network": "none", "read_only_inputs": True}


try:
    evidence = isolation()
except Exception:
    print("REPOPILOT_ISOLATION_FAILED", flush=True)
    sys.exit(125)

print("REPOPILOT_ISOLATION=" + json.dumps(evidence, sort_keys=True), flush=True)
os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
sys.path.insert(0, "/workspace")
import pytest  # noqa: E402 - only after mandatory isolation checks

# Absolute independent test path; ignore project config/plugins and cache writes.
sys.exit(pytest.main(["/validation", "-q", "-s", "-c", "/dev/null", "--confcutdir=/validation", "--import-mode=importlib", "-p", "no:cacheprovider", "--tb=short"]))
