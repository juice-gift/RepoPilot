"""Read-only preflight for the exact V4 Golden fixture; never executes code."""

import hashlib
import re
from datetime import UTC, datetime

from repopilot.config import Settings
from repopilot.github.client import GitHubMCPError, ToolData, connect_github_readonly
from repopilot.github.probe import object_payload
from repopilot.resolution.profiles import FROZEN_MANIFEST_HASH, load_profile

CASES = ("fee-days", "dispatch-preconditions", "ambiguous-cap")


def embedded_source(result: ToolData, repository: str, commit: str, path: str) -> str:
    """Read embedded bytes only; never follow download/resource links."""
    expected_uri = f"repo://{repository}/sha/{commit}/contents/{path}"
    blocks = result.data.get("content")
    if not isinstance(blocks, list):
        raise GitHubMCPError("file_source_unavailable")
    sources = []
    for block in blocks:
        if not isinstance(block, dict) or block.get("type") != "resource":
            continue
        resource = block.get("resource")
        if not isinstance(resource, dict) or resource.get("uri") != expected_uri:
            raise GitHubMCPError("file_identity_mismatch")
        content = resource.get("text")
        if not isinstance(content, str):
            raise GitHubMCPError("file_source_unavailable")
        sources.append(content)
    if len(sources) != 1:
        raise GitHubMCPError("file_source_unavailable")
    return sources[0]


def issue_contract(
    result: ToolData, repository: str, number: int, expected: str
) -> dict[str, object]:
    payload = object_payload(result)
    issue = payload.get("issue")
    if not isinstance(issue, dict) or payload.get("method") != "get":
        raise GitHubMCPError("issue_format_invalid")
    expected_url = f"https://github.com/{repository}/issues/{number}"
    if issue.get("number") != number or issue.get("html_url") != expected_url:
        raise GitHubMCPError("issue_identity_mismatch")
    body = issue.get("body")
    if body is not None and not isinstance(body, str):
        raise GitHubMCPError("issue_format_invalid")
    return {
        "number": number,
        "url": expected_url,
        "body_present": isinstance(body, str) and bool(body.strip()),
        "body_sha256": hashlib.sha256((body or "").encode()).hexdigest(),
        "matches_frozen_contract": isinstance(body, str) and body.strip() == expected,
    }


async def audit_fixture(
    settings: Settings,
    *,
    repository: str,
    expected_commit: str,
    issue_numbers: tuple[int, int, int],
    expected_login: str,
) -> dict[str, object]:
    if not re.fullmatch(r"[0-9a-f]{40}", expected_commit):
        raise GitHubMCPError("commit_required")
    # load_profile verifies every frozen source/test byte against the manifest.
    profiles = [load_profile(case) for case in CASES]
    expected_files = dict(profiles[0].expected_sources)
    async with connect_github_readonly(settings) as reader:
        identity = object_payload(await reader.identity())
        if identity.get("login") != expected_login:
            raise GitHubMCPError("identity_mismatch")
        metadata = object_payload(await reader.repository(repository))
        items = metadata.get("items")
        if (
            metadata.get("total_count") != 1
            or not isinstance(items, list)
            or len(items) != 1
        ):
            raise GitHubMCPError("repository_unverified")
        repo = items[0]
        if not isinstance(repo, dict) or repo.get("full_name") != repository:
            raise GitHubMCPError("repository_identity_mismatch")
        permissions = repo.get("permissions")
        readable = isinstance(permissions, dict) and permissions.get("pull") is True
        default_branch = repo.get("default_branch")
        if default_branch != "main":
            raise GitHubMCPError("baseline_branch_mismatch")
        commit = object_payload(await reader.commit(repository, default_branch))
        actual_commit = commit.get("sha")
        if not isinstance(actual_commit, str) or not re.fullmatch(
            r"[0-9a-f]{40}", actual_commit
        ):
            raise GitHubMCPError("commit_unverified")
        root = (await reader.file(repository, "", actual_commit)).data.get(
            "structured_content"
        )
        if not isinstance(root, list) or len(root) > 100:
            raise GitHubMCPError("root_listing_invalid")
        entries: dict[str, dict[str, object]] = {}
        for entry in root:
            if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
                raise GitHubMCPError("root_listing_invalid")
            path = entry["path"]
            if path in entries:
                raise GitHubMCPError("root_listing_invalid")
            entries[path] = entry
        files = []
        for path, expected_hash in sorted(expected_files.items()):
            observed_hash = None
            if path in entries and entries[path].get("type") == "file":
                text = embedded_source(
                    await reader.file(repository, path, actual_commit),
                    repository,
                    actual_commit,
                    path,
                )
                observed_hash = hashlib.sha256(text.encode()).hexdigest()
            files.append(
                {
                    "path": path,
                    "present": path in entries,
                    "expected_sha256": expected_hash,
                    "observed_sha256": observed_hash,
                    "matches": observed_hash == expected_hash,
                }
            )
        issues = []
        for profile, number in zip(profiles, issue_numbers, strict=True):
            issues.append(
                {
                    "case": profile.case_id,
                    **issue_contract(
                        await reader.issue(repository, number),
                        repository,
                        number,
                        profile.issue,
                    ),
                }
            )
        prs = (await reader.pull_requests(repository)).data.get("structured_content")
        # Report only this bounded first page, never claim an arbitrary complete list.
        if not isinstance(prs, list):
            raise GitHubMCPError("pr_listing_invalid")
        checks = {
            "private_repository": repo.get("private") is True,
            "reported_read_permission": readable,
            "baseline_matches_owner_sha": actual_commit == expected_commit,
            "exact_root_paths": set(entries) == set(expected_files),
            "source_hashes_match": all(file["matches"] for file in files),
            "issue_contracts_match": all(
                issue["matches_frozen_contract"] for issue in issues
            ),
        }
        return {
            "observed_at": datetime.now(UTC).isoformat(),
            "measurement": "actual official GitHub MCP read-only fixture audit",
            "status": "passed" if all(checks.values()) else "blocked_fixture_mismatch",
            "connection": reader.connection_evidence,
            "identity_matches_expected": True,
            "repository": repository,
            "repository_id": repo.get("id"),
            "default_branch": default_branch,
            "expected_commit": expected_commit,
            "actual_commit": actual_commit,
            "checks": checks,
            "files": files,
            "issues": issues,
            "pr_first_page_count": len(prs),
            "pr_page_limit": 10,
            "frozen_manifest_sha256": FROZEN_MANIFEST_HASH,
            "local_independent_validation_integrity": True,
            "remote_test_execution": False,
            "remote_writes": 0,
            "write_permission": "not exercised or authorized; repository role flags do not prove PAT write scopes",
        }
