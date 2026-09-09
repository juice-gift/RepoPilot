# V1 Retrieval Evaluation Results

## Scope

This report records the measured RepoPilot V1 retrieval baseline and the single
improvement retained after inspecting baseline failures. The checked-in Golden
Repository contains 8 supported files and produces 19 code-aware chunks. The
frozen dataset contains 8 natural-language queries with expected file and symbol
evidence.

The run used PostgreSQL + pgvector exact cosine search with the reproducible
`deterministic-token-hash-v1` 512-dimensional provider. These measurements prove
the evaluation and retrieval behavior; they do not represent OpenAI embedding
quality.

## Command

From `apps/api` in PowerShell:

```powershell
$env:PYTHONPATH = "src"
uv run python -m repopilot.evaluation.runner --strategy vector --top-k 5
uv run python -m repopilot.evaluation.runner --strategy hybrid --top-k 5
Remove-Item Env:PYTHONPATH
```

## Measured Results

| Strategy | Hit@1 | Recall@1 | Hit@3 | Recall@3 | Hit@5 | Recall@5 | MRR@5 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Exact vector only | 0.7500 | 0.7500 | 0.8750 | 0.8750 | 1.0000 | 1.0000 | 0.8375 |
| Exact vector + lexical rerank | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

All values above were emitted by the checked-in evaluation runner against the
live migrated development database on 2026-09-09. The integration suite reruns
both strategies and asserts that the retained strategy improves Hit@1 and MRR@5
on the frozen dataset.

## Baseline Failures

- `duplicate-delivery`: expected `src/delivery.py:create_delivery_key` ranked 5.
  The query uses “delivered” while source metadata uses “delivery,” and the
  vector-only local provider did not preserve that relationship strongly.
- `audit-redaction`: expected `src/audit.js:redactAuditFields` ranked 2 behind
  `appendAuditTimestamp`, which shared file-level audit vocabulary but not the
  password/access-token terms.

## Improvement Decision

The retained hybrid strategy still computes exact vector distance for every
indexed chunk. It then combines 70% vector similarity with 30% sparse lexical
cosine similarity over the existing metadata-enriched embedding content.
Identifier splitting, stop-word removal, and small deterministic inflection
normalization make file and symbol vocabulary useful without adding a dependency
or hiding the retrieval behavior.

This change moved both bad cases to rank 1 without regressing the other six cases,
so it was retained and is now the configured default. `RETRIEVAL_STRATEGY=vector`
remains available to reproduce the baseline.

## Limitations

- Eight queries are enough to establish a repeatable V1 baseline, not to claim
  broad code-search quality.
- The deterministic provider is lexical and exists for zero-cost local testing;
  external embedding behavior must be evaluated separately when credentials are
  available.
- Hybrid reranking currently scores every chunk returned by exact search in
  application memory. That is simple and inspectable for V1 repositories but is
  not a large-scale retrieval design.
- The lightweight inflection rules are English-oriented and intentionally do not
  attempt full stemming, synonym expansion, symbol graphs, or V2 Code Intelligence.
