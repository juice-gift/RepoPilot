"""Actual Docker baseline/patch probe; deterministic patching is not LLM evidence."""

import hashlib
import json
import argparse
from pathlib import Path

from repopilot.agent.tools import RunScope
from repopilot.resolution.patch import PatchArguments, PatchEngine, PatchError, actual_diff
from repopilot.resolution.profiles import load_profile
from repopilot.resolution.sandbox import SandboxExecutor
from repopilot.resolution.workspace import SavedSource, Workspace, digest

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "apps/api/evaluation/trusted_python"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["deterministic", "live"], default="deterministic")
    options = parser.parse_args()
    registry = DATA / "profiles.json"
    registry_hash = hashlib.sha256(registry.read_bytes()).hexdigest()
    results = []
    owned_roots = []
    for name in ("itsdangerous", "more-itertools"):
        profile = load_profile("trusted-" + name, registry_path=registry, registry_digest=registry_hash)
        sources = []
        for path in profile.expected_sources:
            text = (DATA / name / "repository" / path).read_text(encoding="utf-8")
            sources.append(SavedSource(path, text, digest(text), len(text.encode())))
        executor = SandboxExecutor(profile.image_id, timeout_seconds=40)
        result = {"repository": profile.repository, "commit": profile.commit_sha,
                  "profile_hash": profile.fingerprint(), "mode": "deterministic-real-docker"}
        with Workspace(RunScope(1, 1), sources) as workspace:
            owned = workspace.root
            owned_roots.append(owned)
            if options.mode == "live":
                from repopilot.config import Settings
                from repopilot.rag.generation import create_agent_provider
                from repopilot.resolution.models import ResolutionRequest
                from repopilot.resolution.runner import run_resolution
                from repopilot.resolution.tools import ResolutionLimits, ResolutionTools

                settings = Settings()
                if settings.generation_provider == "deterministic":
                    raise ValueError("Live mode requires an actual configured model")
                agent = run_resolution(
                    ResolutionRequest(repository_id=1, snapshot_id=1, profile=profile.case_id, issue=profile.issue),
                    tools=ResolutionTools(workspace, profile, executor, ResolutionLimits()),
                    provider=create_agent_provider(settings),
                )
                result["mode"] = "live-llm-real-docker"
                result["agent"] = agent.model_dump(mode="json")
                result["independent_final_test"] = executor.run(workspace, profile).model_dump(mode="json")
                result["workspace_cleaned"] = False
                results.append(result)
                continue
            baseline = executor.run(workspace, profile)
            result["baseline"] = baseline.model_dump(mode="json")
            path = next(iter(profile.editable_paths))
            if name == "itsdangerous":
                old = "            if age > max_age:"
                new = "            if age < 0 or age > max_age:"
            else:
                old = "    windows = windowed(it, window_size)"
                new = "    windows = windowed(it, window_size, fillvalue=_marker)"
            try:
                PatchEngine(workspace, profile.editable_paths, source_evidence_limit=profile.source_evidence_limit).apply(PatchArguments(
                    expected_revision=0, edits=[{"path": path, "old_text": old, "new_text": new}],
                ), attempt=1)
                result["diff"] = actual_diff(workspace)
                result["verification"] = executor.run(workspace, profile).model_dump(mode="json")
            except PatchError as error:
                result["patch_rejected"] = str(error)
        result["workspace_cleaned"] = not owned.exists()
        results.append(result)
    for result, owned in zip(results, owned_roots, strict=True):
        result["workspace_cleaned"] = not owned.exists()
    suffix = "live" if options.mode == "live" else "probe"
    output = ROOT / f"docs/evaluation/pre-v8-python-{suffix}.json"
    output.write_text(json.dumps({"registry_sha256": registry_hash, "cases": results}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps([{k: v for k, v in r.items() if k not in {"baseline", "verification", "diff", "agent", "independent_final_test"}} for r in results], indent=2))


if __name__ == "__main__":
    main()
