"""Explicit exact-output reviews and verified historical provenance."""

import json
from pathlib import Path

from repopilot.config import REPOSITORY_ROOT
from repopilot.evaluation.contracts import CaseResult, digest, file_digest
from repopilot.evaluation.grading import aggregate
from repopilot.evaluation.resolution import review_hash


def apply_reviews(report: dict, reviews: list[dict]) -> dict:
    cases = {c["id"]: c for c in report["cases"]}
    seen = set()
    for review in reviews:
        case = cases.get(review.get("id"))
        if case is None or review["id"] in seen:
            raise ValueError("Unknown or duplicate reviewed task")
        seen.add(review["id"])
        if (
            review.get("evidence_hash") != digest(case["evidence"])
            or not isinstance(review.get("supported"), bool)
            or not review.get("reviewer")
            or not review.get("reason")
            or not review.get("provenance")
        ):
            raise ValueError(
                "Review must identify exact evidence, reviewer, provenance and reason"
            )
        if "claim_support" not in case["checks"]:
            raise ValueError("This task has no claim-support judgment")
        case["checks"]["claim_support"] = "passed" if review["supported"] else "failed"
        case["review"] = review
        if not review["supported"]:
            case["failures"].append("unsupported_final_claims")
            if case["category"] != "resolution":
                case["status"] = "failed"
        elif case["status"] == "unverified" and not case["failures"]:
            case["status"] = "passed"
    report["review_policy"] = digest(reviews)
    report["review_fingerprints"] = {
        name: file_digest(Path(__file__).parent / name)
        for name in ("reviews.py", "grading.py")
    }

    # Reviews are preserved as extra report metadata, not CaseResult schema fields.
    report["aggregate"] = aggregate(
        [
            CaseResult.model_validate({k: v for k, v in c.items() if k != "review"})
            for c in report["cases"]
        ]
    )
    return report


def historical_evidence() -> list[dict]:
    root = REPOSITORY_ROOT / "docs/evaluation"
    reports = []
    report_path = root / "v3-agent-qwen-grounding-report.json"
    reviews_path = root / "v3-agent-qwen-grounding-reviews.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    reviews = json.loads(reviews_path.read_text(encoding="utf-8"))
    for case in report["cases"]:
        result = case["result"]
        payload = {
            "final_answer": result["final_answer"],
            "sources": [
                {
                    k: source[k]
                    for k in (
                        "evidence_id",
                        "file_path",
                        "start_line",
                        "end_line",
                        "content",
                        "truncated",
                    )
                }
                for source in result["sources"]
            ],
        }
        import hashlib

        actual = hashlib.sha256(
            json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()
        review = reviews[case["id"]]
        if actual != review["review_hash"] or actual != case["review_hash"]:
            raise ValueError("Historical V3 review hash mismatch")
        reports.append(
            {
                "id": case["id"],
                "supported": review["grounded"],
                "reason": review["reason"],
                "provenance": "Historical Codex source review, not independent human review; not a V6 run",
                "report": report_path.name,
                "report_hash": file_digest(report_path),
                "review_hash": actual,
                "reviews_file_hash": file_digest(reviews_path),
            }
        )
    path = root / "v4-resolution-qwen-reviews.json"
    for review in json.loads(path.read_text(encoding="utf-8"))["reviews"]:
        original = json.loads((root / review["report"]).read_text(encoding="utf-8"))
        case = next(c for c in original["cases"] if c["id"] == review["case_id"])
        if review_hash(case["result"]) != review["review_hash"]:
            raise ValueError("Historical V4 review hash mismatch")
        reports.append(
            {
                "id": review["case_id"],
                "provenance": review["reviewer"],
                "verdict": review["verdict"],
                "notes": review["notes"],
                "supported": review["final_claims_supported"],
                "report": review["report"],
                "report_hash": file_digest(root / review["report"]),
                "review_hash": review["review_hash"],
            }
        )
    return reports
