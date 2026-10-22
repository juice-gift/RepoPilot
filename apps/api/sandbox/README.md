# V4 local controlled Python test image

Build from the repository root:

```powershell
docker build --tag repopilot-tests:v4 apps/api/sandbox
docker image inspect repopilot-tests:v4 --format '{{.Id}}'
```

The backend uses that immutable local `sha256:` ID, never a model-selected image
or mutable tag. Image preparation requires network access to the official-image
mirror/PyPI; test execution has no network and performs no installations. Python's
base digest and all pytest wheels/versions/hashes are frozen in this directory.
No application dependency or application containerization is introduced.

Run real isolation tests from `apps/api`:

```powershell
$env:RUN_SANDBOX_TESTS='1'
uv run pytest tests/test_resolution_sandbox.py
```

Execution permits only a local Linux engine with seccomp. Containers use UID/GID
65534, no capabilities or privilege escalation, read-only root/input mounts,
network/IPC disabled, one CPU, 256 MiB memory/no swap, 64 processes, 256 file
descriptors and a 32 MiB noexec/nosuid/nodev temporary filesystem. Source and
validation mounts are private per-run directories, never RepoPilot or the Docker
socket. Backend inspection and trusted entrypoint checks happen before importing
fixture code. The public GPG metadata inherited from the official Python image
is allowed; application/provider credentials are never forwarded.

The executor drains stdout/stderr continuously, retaining at most 8000 bytes each,
and disables daemon log retention. It force-removes the exact owned container on
timeout/cancellation and confirms cleanup. All failures remain inspectable and
there is no host-shell fallback. Ordinary tests skip the explicit Docker cases.

These controls reduce risk; Docker shares the host VM kernel and is not an absolute
security boundary for malicious code. V4 supports only the frozen, controlled
Golden source/profile. Passing independent tests is evidence for those expected
behaviors, not a proof of arbitrary patch correctness or resistance to deliberate
test-framework tampering by malicious Python. Inspect the actual diff as well.
