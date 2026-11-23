"""API-container test: deterministic provider, real internal HTTP/DB/Broker/Docker.

Only this test process replaces the model provider. The production Uvicorn process
and its provider configuration remain unchanged. HTTP listener binds container
loopback only, never a published port. No approval or remote write is performed.
"""

import json
import threading
import time
import urllib.request
from pathlib import Path
from unittest.mock import patch

import uvicorn

from repopilot.api.routes import github as routes
from repopilot.config import Settings
from repopilot.evaluation.trusted import ScriptedPythonProvider
from repopilot.main import create_app
from repopilot.resolution.profiles import load_profile

settings = Settings()
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
report = {"mode": "scripted provider; real container-loopback HTTP/API/DB/authenticated Broker/Docker",
          "production_model_provider_unchanged": True, "remote_writes": 0, "cases": []}
server = uvicorn.Server(uvicorn.Config(create_app(settings), host="127.0.0.1", port=8891,
                                     access_log=False, log_level="error"))
thread = threading.Thread(target=server.run)
thread.start()


def call(path, payload=None):
    request = urllib.request.Request("http://127.0.0.1:8891/api/github" + path,
        data=None if payload is None else json.dumps(payload).encode(),
        headers={"Origin": settings.frontend_origin, "Content-Type": "application/json"})
    with opener.open(request, timeout=180) as response:
        return json.load(response)


try:
    deadline = time.monotonic() + 10
    while not server.started and time.monotonic() < deadline:
        time.sleep(0.05)
    assert server.started
    bindings = call("/bindings")
    for identity in ("trusted-itsdangerous", "trusted-more-itertools"):
        profile = load_profile(identity, registry_path=settings.trusted_profile_registry,
                               registry_digest=settings.trusted_profile_registry_sha256)
        binding = next(b for b in bindings if b["profile"] == identity)
        with patch.object(routes, "create_agent_provider", lambda settings: ScriptedPythonProvider(profile)):
            run = call("/runs", {"binding_id": binding["id"]})
        result = run["result"]
        assert result["repair_status"] == "verified_repair" and result["workspace_cleaned"]
        proposal = call("/proposals", {"run_id": run["id"]})
        assert proposal["state"] == "awaiting_approval" and not proposal["approved"]
        # Separate second protected validation from immutable result bytes via Broker.
        from repopilot.agent.tools import RunScope
        from repopilot.resolution.broker_client import create_executor
        from repopilot.resolution.workspace import SavedSource, Workspace, digest

        root = Path("/app/apps/api/evaluation/trusted_python") / identity.removeprefix("trusted-") / "repository"
        baseline = {p: (root / p).read_text() for p in profile.expected_sources}
        saved = [SavedSource(p, c, digest(c), len(c.encode())) for p, c in baseline.items()]
        modified = {**baseline, **{f["path"]: f["modified"] for f in result["changed_files"]}}
        with Workspace(RunScope(result["repository_id"], result["snapshot_id"]), saved) as workspace:
            workspace.publish(modified, 0)
            independent = create_executor(settings).run(workspace, profile)
            assert independent.passed and independent.source_hash == result["test_results"][-1]["source_hash"]
        report["cases"].append({"binding": binding, "run": run, "proposal": proposal,
                                "separate_independent_test": independent.model_dump(mode="json")})
finally:
    server.should_exit = True
    thread.join(10)
    assert not thread.is_alive()
print(json.dumps(report, indent=2))
