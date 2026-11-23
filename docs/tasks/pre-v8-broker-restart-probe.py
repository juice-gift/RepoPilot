"""Host orchestration of test-owned Broker crash recovery; no repository code on host."""

import json
import subprocess
import time

PROJECT = "repopilot-broker-acceptance"
API = PROJECT + "-api-1"
BROKER = PROJECT + "-sandbox-broker-1"


def docker(*args, code=None, check=True):
    return subprocess.run(["docker", *args], input=code, text=True, encoding="utf-8",
                          capture_output=True, timeout=45, check=check)


def api(code):
    return docker("exec", "-i", API, "python", "-", code=code).stdout


competitor = docker("exec", BROKER, "python", "-m", "repopilot.resolution.broker_server", check=False)
assert competitor.returncode != 0 and "BlockingIOError" in competitor.stderr
setup = '''
import json
from pathlib import Path
from uuid import uuid4
from repopilot.config import Settings
from repopilot.resolution.profiles import load_profile
from repopilot.resolution.broker_protocol import BrokerRequest
s=Settings()
p=load_profile('trusted-itsdangerous',registry_path=s.trusted_profile_registry,registry_digest=s.trusted_profile_registry_sha256)
root=Path('/app/apps/api/evaluation/trusted_python/itsdangerous/repository')
baseline={name:(root/name).read_text() for name in p.expected_sources}
path=next(iter(p.editable_paths))
request=BrokerRequest(request_id=uuid4().hex,workspace_id=uuid4().hex,profile=p.case_id,profile_hash=p.fingerprint(),revision=1,baseline=baseline,updates=[{path:'while True:\\n    pass\\n'+baseline[path]}])
Path('/tmp/broker-crash-request.json').write_text(request.model_dump_json())
print(request.request_id)
'''
identity = api(setup).strip()
call = '''
from pathlib import Path
from repopilot.config import Settings
from repopilot.resolution.broker_transport import UnixConnection,read_token
s=Settings()
c=UnixConnection(s.sandbox_broker_socket)
c.request('POST','/v1/tests',Path('/tmp/broker-crash-request.json').read_bytes(),{'Content-Type':'application/json','Authorization':'Bearer '+read_token(s.sandbox_broker_token_file)})
r=c.getresponse()
print(r.status)
r.read(32001)
c.close()
'''
worker = subprocess.Popen(["docker", "exec", "-i", API, "python", "-"],
                          stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          text=True, encoding="utf-8")
worker.stdin.write(call)
worker.stdin.close()
deadline = time.monotonic() + 12
while time.monotonic() < deadline:
    active = docker("ps", "-q", "--filter", "label=repopilot.broker=" + PROJECT).stdout.split()
    if active:
        break
    time.sleep(0.1)
assert len(active) == 1
docker("kill", "--signal", "KILL", BROKER)
worker.wait(timeout=10)
assert worker.returncode != 0
docker("start", BROKER)
deadline = time.monotonic() + 20
while time.monotonic() < deadline:
    health = docker("inspect", BROKER, "--format", "{{.State.Health.Status}}").stdout.strip()
    if health == "healthy":
        break
    time.sleep(0.2)
assert health == "healthy"
assert api(call).strip() == "409"
assert not docker("ps", "-aq", "--filter", "label=repopilot.broker=" + PROJECT).stdout.strip()
check = f'''
import json
from pathlib import Path
assert not list(Path('/execution/workspaces').iterdir())
record=json.loads(Path('/execution/requests/{identity}.json').read_text())
assert record['state']=='pending'
print('owned_orphans_cleaned_pending_identity_preserved')
'''
assert docker("exec", "-i", BROKER, "python", "-", code=check).stdout.strip() == "owned_orphans_cleaned_pending_identity_preserved"
print(json.dumps({"project": PROJECT, "request_id": identity,
                  "checks": ["second_broker_process_lock_denied", "active_broker_killed",
                             "restricted_owned_orphan_removed_on_restart", "private_workspace_cleaned",
                             "pending_request_preserved", "exact_retry_denied_409"],
                  "remote_writes": False}, indent=2))
