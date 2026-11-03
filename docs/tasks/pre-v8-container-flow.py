"""Actual HTTP/MCP/model/Broker/Docker flow through the loopback Web proxy.

No publication approval or remote write endpoint is called. Every attempt is saved.
"""

import argparse
import json
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--base-url", default="http://localhost:8082")
args = parser.parse_args()
if args.output.exists():
    raise SystemExit("Use a new report path to retain every attempt")
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
report = {"mode": "actual Web proxy -> private Unix API -> actual MCP/Qwen -> authenticated Broker -> isolated Docker",
          "runtime_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
          "remote_writes": 0, "checks": [], "cases": []}


def save():
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def call(path, payload=None, origin=None):
    headers = {"Origin": origin or args.base_url}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(args.base_url + path,
        data=None if payload is None else json.dumps(payload).encode(), headers=headers)
    try:
        with opener.open(request, timeout=250) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, json.load(error)


assert call("/api/github/runs", {"binding_id": 1}, origin="https://untrusted.example")[0] == 403
report["checks"].append("wrong_origin_denied_403")
assert call("/api/github/proposals", {"run_id": "0" * 32})[0] == 409
report["checks"].append("private_unix_owner_transport_passes_to_existing_proposal_checks")
save()
for profile in ("trusted-itsdangerous", "trusted-more-itertools"):
    case = {"profile": profile}
    report["cases"].append(case)
    status, binding = call("/api/github/import-trusted", {"profile": profile})
    case.update(import_status=status, binding=binding)
    save()
    if status != 200:
        continue
    print(profile + ": actual MCP binding imported", flush=True)
    status, run = call("/api/github/runs", {"binding_id": binding["id"]})
    case.update(run_status=status, run=run)
    save()
    print(profile + ": actual model run persisted", flush=True)
    if status == 200 and run.get("result", {}).get("repair_status") == "verified_repair":
        status, proposal = call("/api/github/proposals", {"run_id": run["id"]})
        case.update(proposal_status=status, proposal=proposal)
        save()
        assert status == 200 and proposal["state"] == "awaiting_approval" and not proposal["approved"]
        print(profile + ": exact proposal awaiting separate human review", flush=True)
