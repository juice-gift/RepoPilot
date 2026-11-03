# RepoPilot V6 evaluation

Mode: scripted. Scripted protocol only; no real LLM reasoning quality measurement.

Dataset: {'name': 'RepoPilot frozen evaluation suite', 'version': 2, 'hash': '25d0666fe7666424cb84256408b3ae41da7b99fde22c9f3e838c8be5b1f3cc18', 'total_tasks': 17}; selected tasks: 8.

Commit: `4e9f710f4a0b05b94d24b615fcca5ab2475d91d9`; dirty: True; model: frozen-scripts

| Task | Status | Failures |
| --- | --- | --- |
| retrieval/missing-database-url | passed |  |
| retrieval/late-fee-cap | passed |  |
| retrieval/webhook-authentication | passed |  |
| retrieval/duplicate-delivery | passed |  |
| retrieval/tenant-cache-isolation | passed |  |
| retrieval/report-progress | passed |  |
| retrieval/audit-redaction | passed |  |
| retrieval/delivery-backoff | passed |  |

| Metric | Numerator | Denominator | Rate |
| --- | --- | --- | --- |
| task_success | 0 | 0 | None |
| verified_repair | 0 | 0 | None |
| safe_decision | 0 | 0 | None |
| patch_apply | 0 | 0 | None |
| independent_test | 0 | 0 | None |
| evidence_discovery | 8 | 8 | 1.0 |
| citation_validity | 0 | 0 | None |
| citation_identity | 0 | 0 | None |
| claim_support | 0 | 0 | None |
| patch_apply_attempts | 0 | 0 | None |
| retrieval_hit@1 | 6.0 | 8 | 0.75 |
| retrieval_recall@1 | 6.0 | 8 | 0.75 |
| retrieval_mrr@1 | 6.0 | 8 | 0.75 |
| retrieval_hit@3 | 7.0 | 8 | 0.875 |
| retrieval_recall@3 | 7.0 | 8 | 0.875 |
| retrieval_mrr@3 | 6.5 | 8 | 0.8125 |
| retrieval_hit@5 | 8.0 | 8 | 1.0 |
| retrieval_recall@5 | 8.0 | 8 | 1.0 |
| retrieval_mrr@5 | 6.7 | 8 | 0.8375 |

Limitations:

- Three frozen Issue cases cannot establish general repair reliability.
- Tokens/cost unavailable from provider contracts; null is not zero.
- Current answer claim support is unreviewed; valid citations do not prove grounding.
- Historical V3/V4 unsupported claims remain in original reports/reviews.
- One repetition per task; no general accuracy or improvement claim.

Full source/test/patch evidence is in the adjacent JSON. Citation validity does not prove claim support.
