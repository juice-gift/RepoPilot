# RepoPilot V6 evaluation

Mode: live. Actual Qwen decisions; deterministic embeddings.

Dataset: {'name': 'RepoPilot frozen evaluation suite', 'version': 2, 'hash': '25d0666fe7666424cb84256408b3ae41da7b99fde22c9f3e838c8be5b1f3cc18', 'total_tasks': 17}; selected tasks: 2.

Commit: `980325fc1d2b6456ecc32ddedc846298ecf06df8`; dirty: True; model: qwen3.7-flash-2026-07-15

| Task | Status | Failures |
| --- | --- | --- |
| rag/missing-database-url | passed |  |
| rag/late-fee-cap | passed |  |

| Metric | Numerator | Denominator | Rate |
| --- | --- | --- | --- |
| task_success | 0 | 0 | None |
| verified_repair | 0 | 0 | None |
| safe_decision | 0 | 0 | None |
| patch_apply | 0 | 0 | None |
| independent_test | 0 | 0 | None |
| evidence_discovery | 2 | 2 | 1.0 |
| citation_validity | 2 | 2 | 1.0 |
| citation_identity | 2 | 2 | 1.0 |
| claim_support | 2 | 2 | 1.0 |
| patch_apply_attempts | 0 | 0 | None |

Limitations:

- Three frozen Issue cases cannot establish general repair reliability.
- Tokens/cost unavailable from provider contracts; null is not zero.
- Current answer claim support is unreviewed; valid citations do not prove grounding.
- Historical V3/V4 unsupported claims remain in original reports/reviews.
- One repetition per task; no general accuracy or improvement claim.

Full source/test/patch evidence is in the adjacent JSON. Citation validity does not prove claim support.
