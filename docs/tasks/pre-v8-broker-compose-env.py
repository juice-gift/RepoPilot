"""Generate private, test-owned Compose credentials without printing values.

Run with the RepoPilot Python interpreter; output path must be outside the checkout.
Never overwrites an existing deployment. Retain these files for volume restarts.
"""

import argparse
import hashlib
import secrets
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("directory", type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
directory = args.directory.resolve()
if directory.is_relative_to(root) or directory.exists():
    raise SystemExit("Use a new private directory outside the checkout")
directory.mkdir(mode=0o700, parents=True)
token = directory / "broker-token"
with token.open("x", encoding="ascii", newline="\n") as handle:
    handle.write(secrets.token_hex(32) + "\n")
token.chmod(0o600)
password = secrets.token_hex(24)
policy = root / "apps/api/evaluation/trusted_python/profiles.json"
values = {
    "COMPOSE_PROJECT_NAME": "repopilot-broker-acceptance",
    "POSTGRES_PASSWORD": password,
    "POSTGRES_PORT": "55433",
    "WEB_PORT": "8082",
    "CONTAINER_DATABASE_URL": f"postgresql+psycopg://repopilot:{password}@database:5432/repopilot",
    "BROKER_SANDBOX_IMAGE": "sha256:8aa71903f763491db90e2fa2ec4f60944b57aef16dd874aaf8817d43e880d958",
    "BROKER_PROFILE_SHA256": hashlib.sha256(policy.read_bytes()).hexdigest(),
    "BROKER_TOKEN_FILE": token.as_posix(),
}
with (directory / "compose.env").open("x", encoding="utf-8") as handle:
    for key, value in values.items():
        handle.write(f"{key}={value}\n")
(directory / "compose.env").chmod(0o600)
print("Private test deployment files created; no credentials printed")
