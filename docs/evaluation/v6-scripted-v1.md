# RepoPilot V6 evaluation

Mode: scripted. Scripted protocol only; no real LLM reasoning quality measurement.

Dataset: {'name': 'RepoPilot frozen evaluation suite', 'version': 1, 'hash': '8497480d95559a947ed3ae9eb3410a33dea384c0dff026e2abe0a482dac7ddda', 'total_tasks': 17}; selected tasks: 17.

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
| structure/frozen | passed |  |
| investigation/authorization-before-policy | unverified |  |
| investigation/permanent-versus-transient | unverified |  |
| investigation/documentation-policy-mismatch | unverified |  |
| rag/missing-database-url | unverified |  |
| rag/late-fee-cap | unverified |  |
| resolution/fee-days | passed |  |
| resolution/dispatch-preconditions | passed |  |
| resolution/ambiguous-cap | passed |  |

| Metric | Numerator | Denominator | Rate |
| --- | --- | --- | --- |
| task_success | 3 | 3 | 1.0 |
| verified_repair | 2 | 2 | 1.0 |
| safe_decision | 1 | 1 | 1.0 |
| patch_apply | 2 | 2 | 1.0 |
| independent_test | 2 | 2 | 1.0 |
| evidence_discovery | 13 | 13 | 1.0 |
| citation_validity | 5 | 5 | 1.0 |
| citation_identity | 5 | 5 | 1.0 |
| claim_support | 0 | 8 | 0.0 |
| retrieval_hit@1 | 8.0 | 8 | 1.0 |
| retrieval_recall@1 | 8.0 | 8 | 1.0 |
| retrieval_mrr@1 | 8.0 | 8 | 1.0 |
| retrieval_hit@3 | 8.0 | 8 | 1.0 |
| retrieval_recall@3 | 8.0 | 8 | 1.0 |
| retrieval_mrr@3 | 8.0 | 8 | 1.0 |
| retrieval_hit@5 | 8.0 | 8 | 1.0 |
| retrieval_recall@5 | 8.0 | 8 | 1.0 |
| retrieval_mrr@5 | 8.0 | 8 | 1.0 |

Limitations:

- Three frozen Issue cases cannot establish general repair reliability.
- Tokens/cost unavailable from provider contracts; null is not zero.
- Current answer claim support is unreviewed; valid citations do not prove grounding.
- Historical V3/V4 unsupported claims remain in original reports/reviews.
- One repetition per task; no general accuracy or improvement claim.

Full source/test/patch evidence is in the adjacent JSON. Citation validity does not prove claim support.
