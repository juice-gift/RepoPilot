# RepoPilot V6 evaluation

Mode: scripted. Scripted decisions with real Docker; not LLM-quality evidence

Dataset: {'name': 'approved-real-python', 'version': 1, 'hash': '31d498136d014922f7e4eee6675a76282f8c6bfa33b1b0c4b48256fe64967005', 'total_tasks': 3}; selected tasks: 3.

Commit: `59630685f7f5ce6276309f0c0c490d0abf2c51c5`; dirty: True; model: reviewed-python-repairs-v1

| Task | Status | Failures |
| --- | --- | --- |
| python/itsdangerous | passed |  |
| python/more-itertools | passed |  |
| python/ambiguous-clock-drift | passed |  |

| Metric | Numerator | Denominator | Rate |
| --- | --- | --- | --- |
| task_success | 3 | 3 | 1.0 |
| verified_repair | 2 | 2 | 1.0 |
| safe_decision | 1 | 1 | 1.0 |
| patch_apply | 2 | 2 | 1.0 |
| independent_test | 2 | 2 | 1.0 |
| evidence_discovery | 0 | 0 | None |
| citation_validity | 0 | 0 | None |
| citation_identity | 0 | 0 | None |
| claim_support | 0 | 3 | None |
| patch_apply_attempts | 2 | 2 | 1.0 |

Limitations:

- Two small historical issues do not establish general repair accuracy.
- Current provider contracts expose no trustworthy usage/cost; null is unavailable, not zero.
- Protected tests are reviewed local tests, not the complete upstream suites.
- Earlier task-summary Qwen failures remain separate evidence; this corpus uses original Issue bodies.
- No GitHub writes; temporary source/Snapshot records are evaluation-owned and cleaned.

Full source/test/patch evidence is in the adjacent JSON. Citation validity does not prove claim support.
