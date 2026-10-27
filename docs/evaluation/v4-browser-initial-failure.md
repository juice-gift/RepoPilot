# V4 first real Qwen browser run (2026-10-22)

Before evaluation/acceptance, actual browser → resolve API → Qwen `qwen3.7-flash`
at the existing configured provider used the frozen `fee-days` issue. Source was
ingested and indexed through the UI (snapshot `62b425c12e…`, 5 files, 7 chunks).

Observed result: `max_steps`, `execution_status=stopped`,
`repair_status=insufficient_evidence`, revision 0, no changed files, workspace
cleaned. 18 model calls took 79,075 ms. One independent failing baseline ran;
the model submitted a public plan to remove the erroneous overdue-day offset.

Tool sequence: list_files, read_file, run_tests, read_file (error), search_code,
submit_plan, apply_patch (error), read_file, apply_patch (error), apply_patch
(error), apply_patch (error), search_code, apply_patch (error), search_code,
apply_patch (error), apply_patch (error), apply_patch (error), apply_patch (error).

All nine patch calls were rejected before typed validation; the UI showed null
validated arguments and the generic `invalid_or_denied` observation. The old
patch-attempt counter only counted validated dispatch (0), while the model-turn
budget correctly stopped the repeated invalid calls. Raw invalid arguments were
not retained by that version, so their exact schema error cannot be reconstructed
from this trace. This is a real model/tool-interface failure, not repair success.

Follow-up: inspect provider-neutral call arguments in a small non-executing schema
probe, improve precise input/schema feedback without weakening validation, count
invalid patch attempts too, and rerun the same frozen source/issue. Preserve this
failure and distinguish any corrected run from the initial result.

The non-executing real Qwen schema probe returned an `edits` object containing
`description`, `old_string`, and `new_string`, omitting `path`, `old_text`, and
`new_text`. The schema described Edit through a local `$ref`; this probe motivates
inlining the existing Edit fields and adding precise safe schema-error feedback.
This is observed model behavior, not proof that the provider universally rejects
all local JSON Schema references. Backend validation/permissions remain strict.
