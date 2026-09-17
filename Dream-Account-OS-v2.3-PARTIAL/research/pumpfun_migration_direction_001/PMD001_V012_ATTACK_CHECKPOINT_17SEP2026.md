# PMD-001 — V0.12 Attack Checkpoint — 17 Sep 2026

Status: **ACTIVE RESEARCH / EXPLORATORY OUTCOMES POLICY / NO PROMOTION AUTHORITY**

## Current scientific state

- V0.7.1 cross-date exact-chain source: PASS 20/20.
- V0.8 exploratory outcomes were opened by explicit policy amendment; promotion authority remains false.
- Broad 1,012 migration baseline is economically negative after frozen 3.00 pp round-trip stress.
- `migrate_v2` 10-case hint is outlier-dependent and is not an edge.
- V0.10 static-feature autopsy: no robust signal.
- V0.11 aggregate flow snapshot autopsy: source coverage insufficient for final-window flow features; no window rescue authorized.

## Active source attack

GitHub Actions run: `35218989089` — `PMD-001 Chain-Exact Ceiling V07`, run 2.

Frozen prerequisite population:
- rows: 1,012
- dates: 20
- manifest SHA256: `56a8836921b7d348597fa3e63f210adbfe8f34bd67321af797855d23c364243b`
- outcomes opened in ceiling stage: false
- post-price values projected: false

Manifest preparation in run 35218989089: PASS.

Ceiling rule remains unchanged:
- all 1,012 rows must reconcile/source-resolve;
- at least 1,000 rows must contain a successful pre-boundary signature;
- exact V0.7 `migrate` + `migrate_v2` causal boundary semantics;
- no economic outcome is read by the ceiling.

At checkpoint creation, shard 0 (indices 0–252) and shard 1 (253–505) were in progress; shard 2 (506–758) and shard 3 (759–1011) were queued under the frozen runner strategy. No ceiling verdict existed yet.

## V0.12 recipe frozen before full chain data

Authority documents:
- `CHAIN_EXACT_FEATURE_RECIPE_FREEZE_V012.md`
- `CHAIN_EXACT_FEATURE_REPLICATION_GATE_V012.md`

Fixed windows: W30 / W60 / W300 ending strictly before exact chain boundary.

Fixed families include buy/sell counts, participants, SOL volumes, net flow, balance, breadth, trade-size statistics, and two fixed acceleration comparisons. Missing or undecoded flow is never silently treated as zero.

No ML, optimized cutoff, feature subset rescue, or `migrate_v2` cherry-pick is authorized in V0.12.

## Decoder validation

Source-only extractor: `extract_chain_exact_features_v012.py`.

Synthetic parser self-test run `35219809107`: PASS.

Historical real-source compatibility receipt: `V012_HISTORICAL_DECODER_COMPATIBILITY_RECEIPT.md`.
On the original public-RPC historical probe, 4/4 successful exact BUY intents emitted and decoded a valid `TradeEvent`; three failed BUY attempts (`Custom 6005`) emitted no TradeEvent and were correctly not treated as successful economic flow.

## Statistical adjudicator validation

Evaluator: `evaluate_chain_exact_features_v012.py`.

Positive-control run `35220198005`: PASS.
Combined positive + negative control run `35220419689`: PASS.

The evaluator uses Spearman tests, Benjamini-Hochberg FDR over the fixed feature family, chronological-third stability, favorable-quintile diagnostics, trimmed means, and leave-largest-winner-out robustness.

A V0.12 result can only become `V012_REPLICATION_CANDIDATE`; it cannot become an edge/diamond/live setup from this already-opened dataset.

## Prepared continuation — INERT until ceiling VIABLE

Workflow: `.github/workflows/pmd-v012-continuation-from-ceiling.yml`.

It is intentionally untriggered at this checkpoint.
If and only if run `35218989089` produces exact verdict `CHAIN_EXACT_CEILING_V07_VIABLE`, the continuation may be triggered to execute:

1. verify exact ceiling receipt;
2. full 1,012-row V0.7 chain-exact source reconstruction;
3. frozen final Source Gate;
4. V0.12 source-only feature extraction;
5. join to the already-opened frozen V0.8 outcomes;
6. BH-FDR + robustness adjudication.

If the ceiling is complete but `<1000` rows contain successful pre-boundary activity, classify source insufficient and do not trigger full reconstruction. If it is unresolved because of transport/technical errors, only transport-level remediation is allowed; scientific population/rules remain unchanged.

## Forbidden

- merge to main
- live trading / orders / wallets / exchange mutation
- promotion from V0.12 without independent replication
- changing cost stress, horizon, population, source threshold, or windows to save outcomes
- outcome-driven threshold optimization
