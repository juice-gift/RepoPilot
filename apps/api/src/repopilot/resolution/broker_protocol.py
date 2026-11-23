"""Data-only broker contract. Requests never name host paths or execution options."""

from pydantic import BaseModel, ConfigDict, Field

from repopilot.resolution.patch import edit_permitted, source_diff
from repopilot.resolution.profiles import TestProfile
from repopilot.resolution.workspace import WorkspaceError, validate_sources

MAX_REQUEST_BYTES = 8_000_000
MAX_RESPONSE_BYTES = 32_000


class BrokerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    request_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    workspace_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    profile: str = Field(min_length=1, max_length=60, pattern=r"^[a-z0-9-]+$")
    profile_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    revision: int = Field(ge=0, le=8)
    baseline: dict[str, str] = Field(min_length=1, max_length=100)
    updates: list[dict[str, str]] = Field(max_length=8)


def validated_revisions(
    request: BrokerRequest, profile: TestProfile
) -> list[dict[str, str]]:
    if (
        request.profile != profile.case_id
        or request.profile_hash != profile.fingerprint()
        or request.revision != len(request.updates)
    ):
        raise WorkspaceError("Broker profile or revision identity mismatch")
    validate_sources(request.baseline)
    profile.require_snapshot(request.baseline)
    states = [dict(request.baseline)]
    for update in request.updates:
        before = states[-1]
        if (
            not update
            or not update.keys() <= profile.editable_paths
            or any(
                not edit_permitted(p) or p not in before or c == before[p]
                for p, c in update.items()
            )
        ):
            raise WorkspaceError("Broker revision edits are not approved")
        current = {**before, **update}
        validate_sources(current)
        changed_size = sum(
            len(request.baseline[p]) + len(c)
            for p, c in current.items()
            if c != request.baseline[p]
        )
        if (
            len(source_diff(request.baseline, current)) > 40_000
            or changed_size > profile.source_evidence_limit
        ):
            raise WorkspaceError("Broker revision evidence exceeds its approved budget")
        states.append(current)
    return states
