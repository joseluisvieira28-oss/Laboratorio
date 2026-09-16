# PMD-001 — CROSS-DATE V0.4 PASS-IMPOSSIBLE NOTICE

Status: PRE-OUTCOME / FAIL-CLOSED / DOWNSTREAM BLOCKED
Date: 2026-09-16
Branch: `pumpfun-migration-direction-v0.1`
Cross-date run: `35130809897`

## Purpose

This notice records a monotonic gate consequence from already completed mandatory rows. It does **not** replace the final 20-row aggregate receipt and does **not** introduce a new gate or threshold.

`CROSSDATE_PARALLELISM_AMENDMENT_V04.md` froze `BLOCK_FIRST_CROSSDATE_V04_PASS` to require:
- exactly 20 reconciled mandatory rows;
- 20/20 `source_complete == true`;
- 20/20 `feature_source_eligible == true`;
- no substitutions.

Therefore any single mandatory row with either field false makes PASS mathematically impossible, regardless of unfinished rows.

## Completed mandatory failures already observed

### Manifest index 1 — migration date 2026-06-24

Frozen mint:
`QHhbroZxDShtSXm9X2RqjpQP9FvpxbSTUWktPMopump`

Observed source-only facts:
- `safe_in_window_signatures = 0`;
- `same_second_signatures_quarantined = 11`;
- `unique_safe_in_window_slots = 0`;
- `successful_target_pump_transactions = 0`;
- `source_complete = false`;
- `feature_source_eligible = false`;
- `outcomes_opened = false`.

Interpretation under the frozen precision rule: the signatures visible for this selected mint were confined to the integer second containing T0 and therefore were correctly quarantined from `[T0-300s, floor(T0))`.

### Manifest index 5 — migration date 2026-06-28

Frozen mint:
`7N3RPJC7ZxXyEnVyx8i83dcKb9QjMjV34cH2VKjypump`

Observed source-only facts:
- `safe_in_window_signatures = 0`;
- `same_second_signatures_quarantined = 12`;
- `unique_safe_in_window_slots = 0`;
- `successful_target_pump_transactions = 0`;
- `source_complete = false`;
- `feature_source_eligible = false`;
- `outcomes_opened = false`.

Interpretation under the frozen precision rule: the signatures visible for this selected mint were confined to the integer second containing T0 and therefore were correctly quarantined from `[T0-300s, floor(T0))`.

## Monotonic gate consequence

Because mandatory indices 1 and 5 are already non-eligible and substitutions are forbidden:

`BLOCK_FIRST_CROSSDATE_V04_PASS` is impossible for run `35130809897`.

The still-running mandatory rows may refine the final count and distinguish additional source/transport issues, but they cannot restore the frozen 20/20 PASS condition.

## Downstream authority

Until a separately authorized protocol version is frozen **before outcomes** with a materially justified source-access gate, the current frozen chain does not authorize:
- `RUN_SOURCE_GATE_V03.trigger`;
- full 1,012 signature ceiling as a promotion step;
- full block-first reconstruction;
- feature freeze based on this source path;
- any post-migration economic outcome opening.

This is not:
- `NO_EDGE`;
- `NEGATIVE_EXPECTANCY`;
- an economic failure.

Current classification remains a **pre-outcome source/gate failure for the frozen V0.4 cross-date requirement**. The PMD-001 economic hypothesis remains untested.

## Explicitly forbidden rescue

No replacement mint may be selected for 2026-06-24 or 2026-06-28 because the frozen deterministic rule selected exactly one earliest `(T0, mint)` candidate per date.

No same-second signature may be reintroduced after observing this failure.

No reduction of the 20/20 requirement is authorized by this notice.

No economic outcome has been opened.
