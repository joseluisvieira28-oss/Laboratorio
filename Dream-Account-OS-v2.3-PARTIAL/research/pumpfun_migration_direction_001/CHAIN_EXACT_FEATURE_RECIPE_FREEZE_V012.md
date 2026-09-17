# PMD-001 — Chain-Exact Feature Recipe Freeze V0.12

Status: **FROZEN EXPLORATORY RECIPE — NO PROMOTION AUTHORITY**

This document freezes the next feature-extraction attack before the full 1,012-row chain-exact source reconstruction is available.

## Scientific posture

- PMD-001 outcomes were already opened under `EXPLORATORY_OUTCOME_OPENING_POLICY_AMENDMENT_V08.md`.
- Therefore every V0.12 feature/result is exploratory and cannot by itself promote an edge, setup, diamond, or live strategy.
- No post-migration information may enter any V0.12 feature.
- No feature threshold may be selected from economic outcomes.
- No ML/model search is authorized in V0.12.
- Frozen 5-minute outcome construction and 3.00 percentage-point round-trip stress remain unchanged for later exploratory joins.
- The exact causal cutoff is the V0.7 chain boundary `(block_time, slot, transaction_index)`; transactions at or after the boundary are excluded.

## Eligibility prerequisite

Do not execute V0.12 economic discrimination unless the full chain-exact source path reaches its frozen source-coverage requirement. The upstream ceiling remains `>=1000` of 1,012 rows with successful pre-boundary activity and exact source reconciliation.

## Windows

For each source-eligible migration, derive features from three fixed windows ending strictly before the exact chain boundary:

- `W30`: last 30 seconds
- `W60`: last 60 seconds
- `W300`: last 300 seconds

No window may be widened, shifted, or replaced after viewing outcomes.

## Primary flow features

For every window where source reconstruction and transaction decoding are complete:

1. successful target trade count
2. buy count
3. sell count
4. unique buyer wallets
5. unique seller wallets
6. unique participant wallets
7. buy volume in SOL
8. sell volume in SOL
9. net flow in SOL = buy volume - sell volume
10. volume balance = `(buy volume - sell volume) / (buy volume + sell volume)` when denominator > 0
11. count balance = `(buy count - sell count) / trade count` when trade count > 0
12. buy fraction = buy count / trade count
13. wallet breadth = unique participant wallets / trade count
14. average trade SOL
15. median trade SOL
16. largest buy SOL
17. largest sell SOL

All directions and SOL quantities must come from deterministic Pump transaction semantics or authoritative transaction/event fields; ambiguous trades fail closed and are counted as undecoded rather than inferred.

## Acceleration features

Only the following fixed comparisons are authorized:

- per-minute `W60` minus per-minute `W300` for net flow, buy volume, sell volume, trade count, unique participants
- per-second `W30` minus per-second `W60` for the same five quantities

No alternative lag/window optimization is authorized in V0.12.

## Quality / provenance fields

For every migration record, retain:

- exact boundary signature/slot/transaction index
- migration variant (`migrate` or `migrate_v2`)
- counts of raw pre-boundary signatures and successfully decoded target trades
- undecoded/ambiguous target transaction count
- source completeness flags
- first/last decoded trade distance to boundary
- window completeness flag for W30/W60/W300

Rows with unresolved causal order or incomplete source remain in audit receipts but are not silently treated as zero-flow.

## Exploratory outcome analysis after source PASS

For each continuous feature, report without threshold tuning:

- sample size
- Spearman correlation with frozen net 5m return
- fixed quintiles based only on feature rank
- positive-rate, mean, median, trimmed mean, and 1-SOL-each PnL per quintile
- early/middle/late chronological thirds
- result with the single largest positive return removed

A feature is only a **replication candidate**, not an edge, if direction is coherent across chronological thirds and does not depend on one extreme winner. No numerical promotion threshold is introduced here.

## Forbidden rescue

- selecting a cutoff because it maximizes PnL
- selecting only `migrate_v2` because V0.8 looked better
- changing W30/W60/W300 after outcomes
- excluding losers/outliers except for the explicitly reported leave-largest-winner-out robustness diagnostic
- using post-migration price, holder, wallet, or liquidity information as a feature
- treating missing/undecoded activity as zero
- model/feature subset search aimed at maximizing economic outcomes

If no robust separation appears, V0.12 closes as exploratory no-signal rather than spawning threshold rescue.
