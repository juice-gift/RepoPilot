"""Reproduce the V6 source review and offline diagnosis; performs no model calls."""

import json
import subprocess
from pathlib import Path

from repopilot.config import REPOSITORY_ROOT
from repopilot.evaluation.contracts import digest, file_digest, load_dataset
from repopilot.evaluation.grading import resolution_checks
from repopilot.evaluation.harness import DEFINITIONS, save_report
from repopilot.evaluation.reviews import apply_reviews

ROOT = REPOSITORY_ROOT / "docs/evaluation"
PROVENANCE = "Codex source/claim review on 2026-10-29; not independent human review, not a new model run"
REASONS = {
    "investigation/authorization-before-policy": (
        True,
        "workflow.py calls verify_token before retry_delay; auth.py raises PermissionError for invalid token; actual cited ranges and causal ordering match.",
    ),
    "investigation/permanent-versus-transient": (
        False,
        "The answer asserts permanence alone determines rejection and no attempt number raises, contradicting policy.py negative-attempt ValueError and workflow.py token precondition. The summary table also omits these preconditions.",
    ),
    "investigation/documentation-policy-mismatch": (
        False,
        "The 60/300 discrepancy is supported. Claims about why the implementation was designed and that resolution must align documentation lack source support or owner intent. Read-only capability cannot decide the intended contract.",
    ),
    "rag/missing-database-url": (
        True,
        "src/settings.py strips DATABASE_URL, checks emptiness and raises the defined MissingDatabaseUrlError; cited source spans support this answer.",
    ),
    "rag/late-fee-cap": (
        True,
        "src/invoices.py computes max(days,0)//7 weeks at Decimal 0.01, caps the rate at Decimal 0.10 and quantizes balance*rate to Decimal 0.01. The actual weekly calculation/cap/rounding claims are supported. The initial V6-v1 daily annotation was an evaluator error, not an error in this answer.",
    ),
}


def review_report(source: Path, output: Path, *, diagnose: bool = False) -> None:
    report = json.loads(source.read_text(encoding="utf-8"))
    reviews = []
    for case in report["cases"]:
        if case["id"] in REASONS:
            verdict, reason = REASONS[case["id"]]
            reviews.append(
                {
                    "id": case["id"],
                    "evidence_hash": digest(case["evidence"]),
                    "supported": verdict,
                    "reviewer": "Codex",
                    "provenance": PROVENANCE,
                    "reason": reason,
                }
            )
    if diagnose:
        tasks = {t.id: t for t in load_dataset().tasks}
        for index, old in enumerate(report["cases"]):
            if old["category"] == "resolution":
                graded = resolution_checks(tasks[old["id"]], old["evidence"])
                graded.latency_ms = old["latency_ms"]
                report["cases"][index] = graded.model_dump()
    report["source_report"] = {
        "path": source.name,
        "sha256": file_digest(source),
        "definitions": report["definitions"],
        "note": "Original execution dataset/commit/runtime retained. Offline diagnosis changes no execution evidence or dataset identity.",
    }
    report["definitions"] = DEFINITIONS
    report["grading_commit"] = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    report["measurement"] += (
        " Offline source review/diagnosis; no additional model execution."
    )
    report = apply_reviews(report, reviews)
    output.with_name(output.stem + "-reviews.json").write_text(
        json.dumps(reviews, indent=2) + "\n", encoding="utf-8"
    )
    save_report(report, output)


if __name__ == "__main__":
    review_report(
        ROOT / "v6-live-qwen-v1.json",
        ROOT / "v6-live-qwen-v1-diagnosis.json",
        diagnose=True,
    )
    review_report(ROOT / "v6-live-rag.json", ROOT / "v6-live-rag-reviewed.json")
