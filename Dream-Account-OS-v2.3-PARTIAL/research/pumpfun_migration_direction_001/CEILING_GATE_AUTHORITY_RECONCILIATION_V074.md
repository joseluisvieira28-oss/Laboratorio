# PMD-001 — Ceiling Gate Authority Reconciliation V0.7.4

Status: **SOURCE-ONLY / OUTCOME-BLIND / PLUMBING CORRECTION**

This amendment does not change the frozen scientific threshold.

## Pre-existing authority

Before the V0.7.3 distributed result existed:

- `CHAIN_EXACT_FEATURE_RECIPE_FREEZE_V012.md` froze the upstream ceiling requirement as **>=1000 of 1,012 rows with successful pre-boundary activity and exact source reconciliation**.
- `aggregate_chain_exact_source_gate_v07.py` independently froze `MIN_ELIGIBLE = 1000` and does **not** require 1,012 feature-eligible/source-complete rows.

## Implementation mismatch

`aggregate_chain_exact_ceiling_v073.py` added a stricter implementation condition:

`resolved == EXPECTED_ROWS`

That condition was not part of the frozen >=1000 scientific coverage threshold and conflicts with the downstream full source gate.

## V0.7.4 adjudication rule

A ceiling corpus is source-viable only when all of the following hold:

1. all 1,012 frozen manifest indices are present exactly once;
2. all 1,012 mints are unique and non-null;
3. source-only/outcome-wall, parser, transport and receipt contracts reconcile exactly;
4. malformed input count is zero;
5. at least 1,000 rows have `ceiling_has_successful_preboundary_signature = true`.

Rows that are exactly reconciled but fail to resolve a qualifying boundary remain explicit unresolved audit rows. They are never treated as zero-flow and are not feature-eligible.

This amendment does not widen the 300-second window, change parser semantics, alter the population, open outcomes, or lower the >=1000 threshold.
