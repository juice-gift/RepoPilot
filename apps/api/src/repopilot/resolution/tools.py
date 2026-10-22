"""Server permissions and state transitions are independent of model instructions."""

import json
from collections.abc import Callable
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from repopilot.agent.tools import (
    ListFilesArguments,
    ReadFileArguments,
    SearchCodeArguments,
    ToolRegistry,
)
from repopilot.resolution.models import ResolutionObservation, ResolutionPlan
from repopilot.resolution.patch import PatchArguments, PatchEngine, PatchError
from repopilot.resolution.profiles import TestProfile
from repopilot.resolution.reads import WorkspaceReader
from repopilot.resolution.sandbox import SandboxExecutor, TestResult
from repopilot.resolution.workspace import Workspace, WorkspaceError


@dataclass(frozen=True)
class ResolutionLimits:
    model_turns: int = 18
    patch_attempts: int = 4
    test_executions: int = 5
    wall_seconds: float = 180
    context_characters: int = 90_000
    model_output_characters: int = 16_000
    observation_characters: int = 12_000

    def __post_init__(self) -> None:
        if (
            not 1 <= self.model_turns <= 30
            or not 1 <= self.patch_attempts <= 8
            or not 1 <= self.test_executions <= 8
        ):
            raise ValueError("Invalid resolution execution budgets")
        if (
            not 1 <= self.wall_seconds <= 600
            or min(
                self.context_characters,
                self.model_output_characters,
                self.observation_characters,
            )
            < 1000
        ):
            raise ValueError("Invalid resolution time/output budgets")


class RunTestsArguments(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    expected_revision: int = Field(ge=0, le=20)


def bounded(observation: ResolutionObservation, limit: int) -> ResolutionObservation:
    if len(observation.model_dump_json()) <= limit:
        return observation
    original = json.dumps(observation.payload, ensure_ascii=False)
    result = ResolutionObservation(
        status=observation.status, error_code=observation.error_code, truncated=True
    )
    low, high = 0, len(original)
    while low < high:
        middle = (low + high + 1) // 2
        result.payload = {
            "preview": original[:middle],
            "notice": "Truncated untrusted tool data; use smaller reads",
        }
        if len(result.model_dump_json()) <= limit:
            low = middle
        else:
            high = middle - 1
    result.payload = {
        "preview": original[:low],
        "notice": "Truncated untrusted tool data; use smaller reads",
    }
    return result


class ResolutionTools:
    def __init__(
        self,
        workspace: Workspace,
        profile: TestProfile,
        executor: SandboxExecutor,
        limits: ResolutionLimits,
        baseline: ToolRegistry | None = None,
    ) -> None:
        profile.require_snapshot(workspace.baseline)
        if baseline is not None and baseline.scope != workspace.scope:
            raise WorkspaceError("Baseline and workspace scopes differ")
        self.workspace, self.profile, self.executor, self.limits, self.baseline = (
            workspace,
            profile,
            executor,
            limits,
            baseline,
        )
        self.reader = WorkspaceReader(workspace)
        self.patch_engine = PatchEngine(workspace, profile.editable_paths)
        self.plans: list[ResolutionPlan] = []
        self.tests: list[TestResult] = []
        self.patch_attempts = 0
        self.read_paths: set[str] = set()
        self.handlers: dict[str, tuple[type[BaseModel], Callable]] = {
            "list_files": (ListFilesArguments, self.reader.list_files),
            "read_file": (ReadFileArguments, self._read),
            "search_code": (SearchCodeArguments, self.reader.search_code),
            "submit_plan": (ResolutionPlan, self._plan),
            "apply_patch": (PatchArguments, self._patch),
            "run_tests": (RunTestsArguments, self._tests),
        }

    def definitions(self) -> list[dict[str, object]]:
        descriptions = {
            "list_files": "List current workspace files, ordered by path.",
            "read_file": "Read CURRENT modified source at the returned revision. At most 200 lines. Read before planning edits.",
            "search_code": "Literal substring search in CURRENT modified source. No regex or execution.",
            "submit_plan": "Submit a public bounded action plan. Must precede writes. Files must be read and server-approved. Refuse when intent is ambiguous.",
            "apply_patch": "Atomically replace unique exact source text. Supply expected_revision and edits; every edit must include path, old_text, new_text with exactly these field names. Requires repair plan and failing baseline. No tests/config edits.",
            "run_tests": "Run the fixed server-selected independent pytest profile in Docker at expected_revision. No command, image, test or security options are accepted. Run before and after patches.",
        }
        definitions = [
            {
                "type": "function",
                "name": name,
                "description": descriptions[name],
                "parameters": schema.model_json_schema(),
            }
            for name, (schema, _) in self.handlers.items()
        ]
        # Keep this one nested edit schema explicit. The live Qwen probe generated
        # unrelated old_string/new_string fields when Edit was only a local $ref.
        patch_schema = next(
            d["parameters"] for d in definitions if d["name"] == "apply_patch"
        )
        patch_schema["properties"]["edits"]["items"] = patch_schema.pop("$defs")["Edit"]
        if self.baseline:
            for definition in self.baseline.definitions():
                if definition["name"] in {"search_symbol", "retrieve_context"}:
                    definitions.append(
                        {
                            **definition,
                            "description": "BASELINE SNAPSHOT ONLY (may be stale after patches). "
                            + str(definition["description"]),
                        }
                    )
        return definitions

    def execute(
        self, name: str, raw: str, *, remaining_seconds: float
    ) -> tuple[dict[str, object] | None, ResolutionObservation]:
        validated = None
        try:
            if name == "apply_patch":
                if self.patch_attempts >= self.limits.patch_attempts:
                    return None, ResolutionObservation(
                        status="error", error_code="patch_limit"
                    )
                # Invalid schemas are attempts too; do not leave them uncounted.
                self.patch_attempts += 1
            if len(raw) > 36_000:
                raise ValueError("Argument budget exceeded")
            self.workspace.verify()
            if name in {"search_symbol", "retrieve_context"} and self.baseline:
                execution = self.baseline.execute(name, raw, evidence_prefix="B")
                validated = execution.validated_arguments
                observation = ResolutionObservation(
                    status=execution.observation.status,
                    error_code=execution.observation.error_code,
                    payload={
                        "basis": "baseline_snapshot_only",
                        "snapshot_id": self.workspace.scope.snapshot_id,
                        "stale_after_modifications": self.workspace.revision > 0,
                        "evidence": execution.observation.model_dump(mode="json"),
                    },
                )
                return validated, bounded(
                    observation, self.limits.observation_characters
                )
            if name not in self.handlers:
                return None, ResolutionObservation(
                    status="error", error_code="unknown_tool"
                )
            schema, handler = self.handlers[name]
            arguments = schema.model_validate(json.loads(raw))
            validated = arguments.model_dump(mode="json")
            # Reserve execution and forced-cleanup time before starting Docker.
            if name == "run_tests" and remaining_seconds < 65:
                return validated, ResolutionObservation(
                    status="error", error_code="wall_time_limit"
                )
            payload = handler(arguments)
            return validated, bounded(
                ResolutionObservation(payload=payload),
                self.limits.observation_characters,
            )
        except ValidationError as exc:
            errors = [
                {"field": list(error["loc"]), "type": error["type"]}
                for error in exc.errors(include_input=False, include_url=False)[:10]
            ]
            return validated, ResolutionObservation(
                status="error",
                error_code="invalid_arguments",
                payload={
                    "schema_errors": errors,
                    "message": "Use the exact field names and types in the supplied tool schema",
                },
            )
        except PatchError as exc:
            return validated, ResolutionObservation(
                status="error",
                error_code="patch_rejected",
                payload={"message": str(exc)},
            )
        except (ValueError, TypeError, RecursionError) as exc:
            code = (
                str(exc)
                if str(exc) in {"patch_limit", "test_limit", "sandbox_failure"}
                else "invalid_or_denied"
            )
            return validated, ResolutionObservation(
                status="error",
                error_code=code,
                payload={
                    "message": "Arguments, context, plan, baseline or permissions did not satisfy the server rules"
                },
            )
        except Exception:  # noqa: BLE001 - no raw paths, credentials or SDK errors
            return validated, ResolutionObservation(
                status="error", error_code="tool_failure"
            )

    def _read(self, args: ReadFileArguments) -> dict[str, object]:
        result = self.reader.read_file(args)
        self.read_paths.add(args.path)
        return result

    def _plan(self, args: ResolutionPlan) -> dict[str, object]:
        if args.expected_revision != self.workspace.revision or len(
            set(args.files)
        ) != len(args.files):
            raise ValueError("Invalid plan revision or duplicate path")
        if args.decision == "repair":
            if (
                not args.files
                or not set(args.files) <= self.profile.editable_paths
                or not set(args.files) <= self.read_paths
            ):
                raise ValueError("Plan files must be read and permitted")
        elif args.files or self.patch_engine.records:
            raise ValueError("Safe refusal cannot disguise existing changes")
        self.plans.append(args)
        return {"accepted": True, "plan": args.model_dump(mode="json")}

    def _patch(self, args: PatchArguments) -> dict[str, object]:
        if not self.plans or self.plans[-1].decision != "repair":
            raise PatchError("A validated repair plan is required")
        if not {e.path for e in args.edits} <= set(self.plans[-1].files):
            raise PatchError("Patch exceeds the accepted plan")
        if (
            not self.tests
            or self.tests[0].revision != 0
            or self.tests[0].exit_code != 1
            or not self.tests[0].isolation_confirmed
            or self.tests[0].infrastructure_error
        ):
            raise PatchError("A reproducible failing sandboxed baseline is required")
        record = self.patch_engine.apply(args, attempt=self.patch_attempts)
        return {"applied": True, "record": record.model_dump(mode="json")}

    def _tests(self, args: RunTestsArguments) -> dict[str, object]:
        if len(self.tests) >= self.limits.test_executions:
            raise ValueError("test_limit")
        if args.expected_revision != self.workspace.revision:
            raise ValueError("Test revision mismatch")
        result = self.executor.run(self.workspace, self.profile)
        self.tests.append(result)
        if (
            result.infrastructure_error
            or result.timed_out
            or not result.cleanup_confirmed
        ):
            raise ValueError("sandbox_failure")
        return {
            "result": result.model_dump(mode="json"),
            "passed": result.passed,
            "scope": "Independent Golden tests at the exact revision; passing is bounded evidence, not general correctness",
        }
