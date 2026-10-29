"""Fixed Git Data API supplement: immutable objects and create-only branch ref.

The official MCP push_files/create_branch tools cannot bind a write atomically to
an approved parent SHA. No update-ref, default-branch write or generic REST tool
is exposed here. PR creation remains a real MCP tool call.
"""

import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx2

from repopilot.config import Settings
from repopilot.github.client import (
    MAX_RESPONSE_BYTES,
    GitHubMCPError,
    private_transport_logs,
)
from repopilot.github.proposals import PublicationPlan
from repopilot.github.resolution import result_hash


def require_write_scope(
    settings: Settings, plan: PublicationPlan, approved_hash: str | None
) -> None:
    if (
        plan.repository not in settings.github_write_allowed_repositories
        or plan.repository not in settings.github_mcp_allowed_repositories
        or approved_hash != result_hash(plan.model_dump(mode="json"))
        or plan.head_branch != f"codex/issue-{plan.issue_number}-{plan.proposal_id}"
        or plan.base_branch != "main"
    ):
        raise GitHubMCPError("publication_not_authorized")


class GitObjects:
    def __init__(self, http: httpx2.AsyncClient, plan: PublicationPlan) -> None:
        self.http, self.plan = http, plan
        self.calls = 0

    @property
    def write_payloads(self) -> dict[str, dict]:
        p = self.plan
        actor = {"name": p.author_name, "email": p.author_email, "date": p.commit_date}
        return {
            "git/trees": {
                "tree": [
                    {"path": path, "mode": "100644", "type": "blob", "content": text}
                    for path, text in sorted(p.files.items())
                ]
            },
            "git/commits": {
                "message": p.commit_message,
                "tree": p.tree_sha,
                "parents": [p.base_sha],
                "author": actor,
                "committer": actor,
            },
            "git/refs": {"ref": f"refs/heads/{p.head_branch}", "sha": p.commit_sha},
        }

    async def _request(
        self, method: str, resource: str, payload: dict | None = None
    ) -> dict | None:
        p = self.plan
        allowed_reads = {
            "",
            "git/ref/heads/main",
            f"git/ref/heads/{p.head_branch}",
            f"git/commits/{p.base_sha}",
            f"git/commits/{p.commit_sha}",
            f"git/trees/{p.tree_sha}",
        }
        allowed_writes = {"git/trees", "git/commits", "git/refs"}
        if not (
            (method == "GET" and resource in allowed_reads)
            or (
                method == "POST"
                and resource in allowed_writes
                and payload == self.write_payloads[resource]
            )
        ):
            raise GitHubMCPError("git_operation_denied")
        self.calls += 1
        if self.calls > 32:
            raise GitHubMCPError("git_call_limit")
        url = f"https://api.github.com/repos/{p.repository}" + (
            f"/{resource}" if resource else ""
        )
        try:
            async with self.http.stream(method, url, json=payload) as response:
                if method == "GET" and response.status_code == 404 and resource != "":
                    return None
                if response.status_code not in {200, 201}:
                    code = {
                        401: "authentication_failed",
                        403: "permission_denied",
                        409: "git_conflict",
                        422: "git_conflict",
                    }.get(response.status_code, "git_request_failed")
                    raise GitHubMCPError(code)
                if (
                    response.headers.get("content-encoding", "identity").lower()
                    != "identity"
                ):
                    raise GitHubMCPError("encoding_denied")
                raw = bytearray()
                async for chunk in response.aiter_bytes():
                    raw.extend(chunk)
                    if len(raw) > MAX_RESPONSE_BYTES:
                        raise GitHubMCPError("response_limit")
                result = json.loads(raw)
                if not isinstance(result, dict):
                    raise GitHubMCPError("git_response_invalid")
                return result
        except GitHubMCPError:
            raise
        except Exception:  # noqa: BLE001 - never expose credential-bearing network errors
            raise GitHubMCPError(
                "git_transport_ambiguous" if method == "POST" else "git_read_failed"
            ) from None

    async def metadata(self) -> dict:
        return await self._request("GET", "")

    async def ref(self, branch: str) -> dict | None:
        return await self._request("GET", f"git/ref/heads/{branch}")

    async def tree(self) -> dict | None:
        return await self._request("GET", f"git/trees/{self.plan.tree_sha}")

    async def commit(self, *, baseline: bool = False) -> dict | None:
        return await self._request(
            "GET",
            f"git/commits/{self.plan.base_sha if baseline else self.plan.commit_sha}",
        )

    async def create_tree(self) -> dict:
        return await self._request(
            "POST", "git/trees", self.write_payloads["git/trees"]
        )

    async def create_commit(self) -> dict:
        return await self._request(
            "POST", "git/commits", self.write_payloads["git/commits"]
        )

    async def create_branch(self) -> dict:
        return await self._request("POST", "git/refs", self.write_payloads["git/refs"])


@asynccontextmanager
async def _git_session(
    settings: Settings, plan: PublicationPlan
) -> AsyncIterator[GitObjects]:
    if plan.repository not in settings.github_mcp_allowed_repositories:
        raise GitHubMCPError("repository_denied")
    secret = settings.github_mcp_token
    if secret is None:
        raise GitHubMCPError("credential_missing")
    token = secret.get_secret_value()
    if not token or any(ord(c) < 33 or ord(c) > 126 for c in token):
        raise GitHubMCPError("credential_invalid")
    with private_transport_logs():
        async with httpx2.AsyncClient(
            headers={
                "Authorization": "Bearer " + token,
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2026-03-10",
                "Accept-Encoding": "identity",
            },
            timeout=20,
            follow_redirects=False,
            trust_env=False,
        ) as http:
            yield GitObjects(http, plan)


@asynccontextmanager
async def connect_git_objects(
    settings: Settings, plan: PublicationPlan, approved_hash: str
) -> AsyncIterator[GitObjects]:
    require_write_scope(settings, plan, approved_hash)
    async with _git_session(settings, plan) as client:
        yield client


async def read_git_baseline(settings: Settings, plan: PublicationPlan) -> dict:
    """Only four fixed GETs: no object/ref creation and no implicit retries."""
    async with _git_session(settings, plan) as git:
        return {
            "repository": await git.metadata(),
            "base_ref": await git.ref("main"),
            "base_commit": await git.commit(baseline=True),
            "head_ref": await git.ref(plan.head_branch),
        }
