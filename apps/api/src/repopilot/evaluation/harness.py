"""Unified frozen evaluation CLI. No remote mutation capabilities."""

import argparse
import json
import platform
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from repopilot.config import REPOSITORY_ROOT, Settings
from repopilot.evaluation.adapters import execute, owned_inputs
from repopilot.evaluation.contracts import CaseResult, digest, file_digest, load_dataset
from repopilot.evaluation.grading import aggregate
from repopilot.evaluation.reviews import apply_reviews, historical_evidence

DEFINITIONS = "v6-evidence-grading-1"


def save_report(report: dict, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# RepoPilot V6 evaluation",
        "",
        f"Mode: {report['mode']}. {report['measurement']}",
        "",
        f"Dataset: {report['dataset']}; selected tasks: {len(report['selection'])}.",
        "",
        f"Commit: `{report['code_commit']}`; dirty: {report['dirty']}; model: {report['runtime']['model']}",
        "",
        "| Task | Status | Failures |",
        "| --- | --- | --- |",
    ]
    lines += [
        f"| {c['id']} | {c['status']} | {', '.join(c['failures'])} |"
        for c in report["cases"]
    ]
    lines += [
        "",
        "| Metric | Numerator | Denominator | Rate |",
        "| --- | --- | --- | --- |",
    ]
    lines += [
        f"| {k} | {v['numerator']} | {v['denominator']} | {v['rate']} |"
        for k, v in report["aggregate"]["metrics"].items()
    ]
    lines += ["", "Limitations:", ""] + ["- " + item for item in report["limitations"]]
    lines += [
        "",
        "Full source/test/patch evidence is in the adjacent JSON. Citation validity does not prove claim support.",
    ]
    output.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def failure_result(task, error: Exception) -> CaseResult:
    name = type(error).__name__
    provider = name in {
        "GenerationConfigurationError",
        "GenerationFailedError",
        "AuthenticationError",
        "RateLimitError",
        "APIConnectionError",
        "APIStatusError",
    }
    checks = (
        {
            "verified_repair": "not_run",
            "independent_test": "not_run",
            "patch_apply": "not_run",
        }
        if task.expected == "verified_repair"
        else {"safe_decision": "not_run"}
        if task.expected == "needs_owner_decision"
        else {"evidence_discovery": "not_run"}
    )
    return CaseResult(
        id=task.id,
        category=task.category,
        status="provider_error" if provider else "infrastructure_error",
        checks=checks,
        failures=["provider_failure" if provider else "sandbox_infrastructure_failure"],
        evidence={
            "error_type": name,
            "expected": task.evidence,
            "detail": "Exception text omitted for secret safety.",
        },
    )


def run(
    settings: Settings,
    *,
    mode: str,
    output: Path,
    categories: list[str] | None = None,
    selected: list[str] | None = None,
    strategy: str = "hybrid",
    dataset_path: Path | None = None,
) -> dict:
    if mode not in {"scripted", "live"} or strategy not in {"vector", "hybrid"}:
        raise ValueError("Invalid mode or strategy")
    dataset = load_dataset(dataset_path) if dataset_path else load_dataset()
    if categories and not set(categories) <= {t.category for t in dataset.tasks}:
        raise ValueError("Unknown category")
    if selected is not None and (
        not selected
        or len(selected) != len(set(selected))
        or not set(selected) <= {t.id for t in dataset.tasks}
    ):
        raise ValueError("Unknown, empty or duplicate selection")
    tasks = [
        t
        for t in dataset.tasks
        if (not categories or t.category in categories)
        and (not selected or t.id in selected)
    ]
    if not tasks:
        raise ValueError("Empty task selection")

    def git(*args):
        return subprocess.run(
            ["git", *args],
            cwd=REPOSITORY_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

    report = {
        "schema_version": 1,
        "historical_evidence": historical_evidence(),
        "review_policy": "unreviewed",
        "definitions": DEFINITIONS,
        "dataset": {
            "name": dataset.name,
            "version": dataset.version,
            "hash": digest(dataset.model_dump()),
            "total_tasks": len(dataset.tasks),
        },
        "selection": [t.id for t in tasks],
        "mode": mode,
        "measurement": "Actual Qwen decisions; deterministic embeddings."
        if mode == "live"
        else "Scripted protocol only; no real LLM reasoning quality measurement.",
        "code_commit": git("rev-parse", "HEAD"),
        "dirty": bool(git("status", "--porcelain")),
        "started_at": datetime.now(UTC).isoformat(),
        "runtime": {
            "model": settings.qwen_generation_model
            if mode == "live"
            else "frozen-scripts",
            "provider": "qwen" if mode == "live" else "scripted",
            "retrieval_strategy": strategy,
            "embedding": "deterministic-token-hash",
            "top_k": 5,
            "max_output_tokens": settings.generation_max_output_tokens,
            "endpoint_hash": digest(settings.dashscope_base_url)
            if mode == "live"
            else None,
            "sandbox_image": settings.resolution_sandbox_image,
            "python": platform.python_version(),
            "platform": platform.system(),
            "fingerprints": {
                name: file_digest(REPOSITORY_ROOT / "apps/api/src/repopilot" / name)
                for name in (
                    "agent/runner.py",
                    "resolution/service.py",
                    "rag/generation.py",
                    "evaluation/grading.py",
                    "evaluation/adapters.py",
                    "evaluation/harness.py",
                )
            },
        },
        "cases": [],
        "aggregate": aggregate([]),
        "limitations": [
            "Three frozen Issue cases cannot establish general repair reliability.",
            "Tokens/cost unavailable from provider contracts; null is not zero.",
            "Current answer claim support is unreviewed; valid citations do not prove grounding.",
            "Historical V3/V4 unsupported claims remain in original reports/reviews.",
            "One repetition per task; no general accuracy or improvement claim.",
        ],
    }
    save_report(report, output)
    results = []
    for task in tasks:
        started = perf_counter()
        try:
            with owned_inputs(settings) as root:
                case = execute(task, settings, mode, strategy, root)
        except Exception as error:  # noqa: BLE001 -- persist per-case failure, continue bounded selection
            case = failure_result(task, error)
        case.latency_ms = round((perf_counter() - started) * 1000, 3)
        results.append(case)
        report["cases"] = [c.model_dump() for c in results]
        report["aggregate"] = aggregate(results)
        save_report(report, output)
        print(f"{task.id}: {case.status}", flush=True)
    report.update(
        finished_at=datetime.now(UTC).isoformat(), complete=len(results) == len(tasks)
    )
    save_report(report, output)
    return report


def compare(left: dict, right: dict) -> dict:
    for key in (
        "schema_version",
        "definitions",
        "dataset",
        "selection",
        "mode",
        "runtime",
        "review_policy",
    ):
        if left.get(key) != right.get(key):
            raise ValueError(f"Incompatible runs: {key}")
    for report in (left, right):
        if (
            not report.get("complete")
            or [c["id"] for c in report["cases"]] != report["selection"]
        ):
            raise ValueError("Incomplete run")
        if (
            aggregate(
                [
                    CaseResult.model_validate(
                        {k: v for k, v in c.items() if k != "review"}
                    )
                    for c in report["cases"]
                ]
            )
            != report["aggregate"]
        ):
            raise ValueError("Aggregate does not match case evidence")
    return {
        "compatible": True,
        "case_changes": [
            {"id": a["id"], "before": a["status"], "after": b["status"]}
            for a, b in zip(left["cases"], right["cases"], strict=True)
            if a["status"] != b["status"]
        ],
        "metrics": {
            k: {"before": v, "after": right["aggregate"]["metrics"][k]}
            for k, v in left["aggregate"]["metrics"].items()
        },
        "limitations": "Single-run differences do not establish reliability or statistical improvement.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    execution = sub.add_parser("run")
    execution.add_argument("--mode", choices=["scripted", "live"], default="scripted")
    execution.add_argument(
        "--category",
        action="append",
        choices=["retrieval", "structure", "investigation", "rag", "resolution"],
    )
    execution.add_argument("--case", action="append")
    execution.add_argument("--strategy", choices=["vector", "hybrid"], default="hybrid")
    execution.add_argument("--dataset", type=Path)
    execution.add_argument("--output", type=Path, required=True)
    comparison = sub.add_parser("compare")
    comparison.add_argument("left", type=Path)
    comparison.add_argument("right", type=Path)
    comparison.add_argument("--output", type=Path, required=True)
    review_parser = sub.add_parser("review")
    review_parser.add_argument("report", type=Path)
    review_parser.add_argument("reviews", type=Path)
    review_parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "review":
        result = apply_reviews(
            json.loads(args.report.read_text(encoding="utf-8")),
            json.loads(args.reviews.read_text(encoding="utf-8")),
        )
        save_report(result, args.output)
    elif args.command == "compare":
        result = compare(
            json.loads(args.left.read_text(encoding="utf-8")),
            json.loads(args.right.read_text(encoding="utf-8")),
        )
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    else:
        report = run(
            Settings(),
            mode=args.mode,
            output=args.output,
            categories=args.category,
            selected=args.case,
            strategy=args.strategy,
            dataset_path=args.dataset,
        )
        if any(
            c["status"] in ("failed", "provider_error", "infrastructure_error")
            for c in report["cases"]
        ):
            raise SystemExit(1)


if __name__ == "__main__":
    main()
