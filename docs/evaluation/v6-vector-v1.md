# RepoPilot V6 evaluation

Mode: scripted. Scripted protocol only; no real LLM reasoning quality measurement.

Dataset: {'name': 'RepoPilot frozen evaluation suite', 'version': 1, 'hash': '8497480d95559a947ed3ae9eb3410a33dea384c0dff026e2abe0a482dac7ddda', 'total_tasks': 17}; selected tasks: 8.

Commit: `4b3c2b0681c7f8fbe0c4cccc707e62f4597d736d`; dirty: True; model: frozen-scripts

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
