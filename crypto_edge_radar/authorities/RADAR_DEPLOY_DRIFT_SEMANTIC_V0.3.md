# CRYPTO EDGE RADAR — DEPLOY DRIFT SEMANTIC CLASSIFIER V0.3

Date: 2026-09-23
Status: OPERATIONAL OBSERVABILITY ONLY / FROZEN BEFORE CODE CHANGE

## Problem

V0.1/V0.2 compare Render RENDER_GIT_COMMIT to the canonical branch head.
That correctly detects commit drift, but a branch-head change containing only
non-runtime artifacts (for example receipts or tests) can produce a false
STALE_RUNTIME alarm and unnecessary redeploy pressure.

## Conservative V0.3 rule

When deployed commit != canonical head:

1. Fetch the public GitHub compare diff between deployed commit and head.
2. Parse only changed file paths from `diff --git a/<path> b/<path>`.
3. A mismatch may be classified
   `IN_SYNC_RUNTIME_CODE__NON_RUNTIME_BRANCH_DRIFT`
   only when:
   - the compare diff is successfully retrieved;
   - at least one changed file is identified; and
   - EVERY changed file lies under an explicitly safe non-runtime prefix.

Frozen safe non-runtime prefixes:
- `.github/workflows/`
- `crypto_edge_radar/receipts/`
- `crypto_edge_radar/tests/`

Everything else is runtime-relevant or ambiguous and remains:
`STALE_RUNTIME`.

Authority files are deliberately NOT ignored because runtime code may read them.
Assets/config/package files are deliberately NOT ignored.

If compare-diff retrieval/parsing fails, fail conservatively as
`STALE_RUNTIME`; never infer semantic equivalence.

## Meaning

`IN_SYNC_RUNTIME_CODE__NON_RUNTIME_BRANCH_DRIFT` means only that the deployed
runtime code is not known to differ from canonical based on the frozen safe-path
rule. It does NOT mean git heads are equal.

The receipt must expose:
- deployed_commit
- canonical_head_commit
- git_head_equal
- runtime_code_in_sync
- changed_files
- compare source/error where applicable.

## Firewalls

automatic_deploy=false
science_changed=false
signal_changed=false
timing_changed=false
costs_changed=false
database_mutation=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
capital=false
main_merge=false
