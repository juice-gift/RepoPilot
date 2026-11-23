# Pre-V8 execution plan — closed 2026-11-03

Authorization: [Goal](../goals/pre-v8-engineering.md) and the owner's explicit
trusted-repository / constrained Broker approvals. Branch `codex/pre-v8-engineering`,
baseline 40ccf6f. Final application code ecbc22b. **Stop before V8.**

| Milestone | Final state | Evidence |
| --- | --- | --- |
| M0 preflight | Complete | Original V4–V6 inspected; clean baseline, read-only origin/main fetch 5316cf8; original 373-pass live baseline |
| A packaging/config/CI | Complete locally | Locked API/Web/Broker images, explicit config, safe contexts, migrations; hosted CI unexecuted |
| A diagnostics/reliability/deployment | Complete for tested scope | JSON correlation, bounded providers/tests, exact recovery, fresh volumes, both deployment modes, restart preservation and backup/restore |
| B trusted Python generalization | Complete within audited root/src projections | ItsDangerous #126 and more-itertools #1336 at fixed commits; immutable source/tests/image, success/failure/refusal and original Golden regression |
| C integration/review/publication contracts | Complete locally | Actual MCP reads, real HTTP/DB/Broker/Docker scripted repairs, separate retests, durable exact proposals, browser review and fake-remote recovery; no new remote writes |
| Broker approved boundary | Implemented and validated | Fixed profiles; authenticated private Unix transport; private data/IPC volumes; path/link/resource validation; request ledger/process lock; unauthorized/concurrent/timeout/crash checks |
| D regression/evaluation/security/docs | Complete with recorded limitations | 464 passed /1 optional online MCP skip, Ruff/build/audit/migrations/current images, final frozen and trusted CLI, security/scope audit and completion report |

## Final validation

- Full DB/Sandbox/trusted pytest on ecbc22b: **464 passed /1 skipped**, 178.28s.
  Existing Starlette/AnyIO deprecation warning remains. Ruff and Alembic head/check
  pass; disposable replay/pgvector/sentinel/reverse migration is covered.
- TypeScript/Vite build passes; npm audit reports zero findings.
- Current API/Web/Broker images build and start. New `repopilot-broker-clean`
  volumes/DB support Broker and basic deployment modes: each smoke yields repo/
  snapshot 1, 19 chunks and one deterministic citation. Separate reviewed-image
  runtime policy passes both repairs/retests without changing historical fixtures.
- Actual Broker authentication/profile/path/command/oversize/framing/link denial,
  absolute input deadline, one-job concurrency and real 20-second timeout pass.
  Force-kill/restart cleans only verified owned resources, preserves ambiguous
  request identities and denies replay. App restart preserves two bindings/four
  runs and exact hashes; no API/Web daemon access or owned test-container residue.
- Final V6 frozen CLI: 12 passed /5 semantic outputs unverified. First closing
  attempt omitted the image setting and produced three infrastructure errors;
  preserved separately, then corrected and rerun with the frozen immutable image.
- Final trusted-python scripted CLI: 3/3, including zero-change owner decision.
  Earlier actual original-Issue Qwen harness success and unsupported prose remain.
  Current actual Web/container Qwen attempts both hit max_steps at revision zero;
  no tuning/selective retry was used. Deterministic and live evidence stay separate.
- Two actual container HTTP scripted repairs and separate protected retests pass
  8/8 and 9/9. Exact proposals e1acb0e716fe4d059c2f9231813a2063 /
  6107aafaa53b40bcb0b770af598bcf63 remain awaiting approval; browser verifies review.
- Security scan: no provider/Broker/new-deployment secret in repository files,
  logs or image config. The original development DB uses a public template
  credential matching three pre-existing template/test files; retained as a known
  local-development limitation. No existing credentials were changed.
- Backup/restore into NEW DB earlier verified 17 Snapshot rows and equal aggregate
  387b77cc39bee8ca0267329d514eec1d. No original data/volume was removed.

## Closure and limits

[Completion/criterion audit](../evaluation/pre-v8-engineering-completion.md),
[security audit](../evaluation/pre-v8-security-review.md),
[deployment](../deployment.md), [Python review](../evaluation/pre-v8-python-review.md).

Hosted CI and independent human semantic review remain unexecuted; new remote
publication/public hosting remain unauthorized. Broker has local Docker authority
and is verified on Windows Docker Desktop's Linux engine/socket group 0. This
single-owner local system has no public or hostile multi-tenant security claim.
No unresolved blocking engineering defect remains within the authorized scope.

The clean verification project is stopped with volumes retained. Original stack
retained; accepted localhost:8082 review stack remains available. No automatic work,
new tuning, feature expansion or V8 work follows this closure.

Meaningful local commits: e864545, aeb0e69, bcd7b03, 544f741, b7d5f82, 8b97521,
29fd645, 270e8d7, 5963068, 9a9286b, 461d0b7 (then-incomplete audit), 47807f2
(Broker approval), 82f1664, 0377114, ecbc22b; closing evidence/docs committed separately.
Historical milestone observations and failures remain in Git and raw reports.
No Python package/schema/framework/queue was added. Docker CLI is restricted to
Broker; npm lock security updates are recorded. No push, merge or remote mutation.