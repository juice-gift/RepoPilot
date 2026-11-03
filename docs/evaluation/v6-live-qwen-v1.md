# RepoPilot V6 evaluation

Mode: live. Actual Qwen decisions; deterministic embeddings.

Dataset: {'name': 'RepoPilot frozen evaluation suite', 'version': 1, 'hash': '8497480d95559a947ed3ae9eb3410a33dea384c0dff026e2abe0a482dac7ddda', 'total_tasks': 17}; selected tasks: 8.

Commit: `4b3c2b0681c7f8fbe0c4cccc707e62f4597d736d`; dirty: True; model: qwen3.7-flash-2026-07-15

| Task | Status | Failures |
| --- | --- | --- |
| investigation/authorization-before-policy | unverified |  |
| investigation/permanent-versus-transient | unverified |  |
| investigation/documentation-policy-mismatch | unverified |  |
| rag/missing-database-url | unverified |  |
| rag/late-fee-cap | unverified |  |
| resolution/fee-days | passed |  |
| resolution/dispatch-preconditions | failed | agent_limit_exhaustion, independent_test_failure |
| resolution/ambiguous-cap | passed |  |

| Metric | Numerator | Denominator | Rate |
| --- | --- | --- | --- |
| task_success | 2 | 3 | 0.6666666666666666 |
| verified_repair | 1 | 2 | 0.5 |
| safe_decision | 1 | 1 | 1.0 |
| patch_apply | 2 | 2 | 1.0 |
| independent_test | 2 | 2 | 1.0 |
| evidence_discovery | 5 | 5 | 1.0 |
| citation_validity | 5 | 5 | 1.0 |
| citation_identity | 5 | 5 | 1.0 |
| claim_support | 0 | 8 | 0.0 |

Limitations:

- Three frozen Issue cases cannot establish general repair reliability.
- Tokens/cost unavailable from provider contracts; null is not zero.
- Current answer claim support is unreviewed; valid citations do not prove grounding.
- Historical V3/V4 unsupported claims remain in original reports/reviews.
- One repetition per task; no general accuracy or improvement claim.

Full source/test/patch evidence is in the adjacent JSON. Citation validity does not prove claim support.
