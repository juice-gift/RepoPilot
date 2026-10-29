# RepoPilot V6 evaluation

Mode: scripted. Scripted protocol only; no real LLM reasoning quality measurement.

Dataset: {'name': 'RepoPilot frozen evaluation suite', 'version': 1, 'hash': '8497480d95559a947ed3ae9eb3410a33dea384c0dff026e2abe0a482dac7ddda', 'total_tasks': 17}; selected tasks: 2.

Commit: `d95f69840c202ee66064fb30b68ffe66e85f6fc4`; dirty: True; model: frozen-scripts

| Task | Status | Failures |
| --- | --- | --- |
| rag/missing-database-url | failed | unsupported_citation |
| rag/late-fee-cap | failed | unsupported_citation |

| Metric | Numerator | Denominator | Rate |
| --- | --- | --- | --- |
| task_success | 0 | 0 | None |
| verified_repair | 0 | 0 | None |
| safe_decision | 0 | 0 | None |
| patch_apply | 0 | 0 | None |
| independent_test | 0 | 0 | None |
| evidence_discovery | 2 | 2 | 1.0 |
| citation_validity | 0 | 2 | 0.0 |
| citation_identity | 0 | 2 | 0.0 |
| claim_support | 0 | 2 | 0.0 |

Limitations:

- Three frozen Issue cases cannot establish general repair reliability.
- Tokens/cost unavailable from provider contracts; null is not zero.
- Current answer claim support is unreviewed; valid citations do not prove grounding.
- Historical V3/V4 unsupported claims remain in original reports/reviews.
- One repetition per task; no general accuracy or improvement claim.

Full source/test/patch evidence is in the adjacent JSON. Citation validity does not prove claim support.
