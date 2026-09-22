# AMM-LVR-CROSSVENUE-001 — PRE-DISCOVERY FREEZE V0.1

**Status:** FROZEN BEFORE INTERNAL ECONOMIC OUTCOMES  
**Date:** 2026-09-22  
**Primary family:** RV  
**Secondary family:** MICRO  
**Mode:** Research-only / fail-closed

## 1. Mechanism

A CEX price move can leave an AMM temporarily stale. Arbitrageurs trade against the stale AMM price and hedge/rebalance on the CEX. The economic transfer is adverse selection borne by passive AMM liquidity providers. The mechanism is not "DEX price predicts CEX price"; it is cross-venue convergence with a mechanically stale on-chain quote.

## 2. Anti-duplication

Repository searches before branch creation returned no existing exact LVR or CEX-DEX arbitrage lab. This is materially distinct from DEX-LIQUIDITY-PROVISION-001, whose frozen mechanism is LP provision/withdrawal state -> future volatility/impact. AMM-LVR-CROSSVENUE-001 instead tests stale AMM price -> cross-venue arbitrage extraction -> realizable searcher PnL.

No promotion credit transfers from any prior lab.

## 3. Known evidence contamination map

Before this freeze, external published evidence was already known:
- CEX-DEX arbitrage exists at large scale on Ethereum.
- The 2025 AFT study reports 7,203,560 identified arbitrages and USD 233.8M estimated extracted value from 19 labeled searchers over 2023-08-08 to 2025-03-08.
- Searcher market share is concentrated and builder integration matters.
- Published PnL is explicitly an upper-bound estimate because off-chain hedge price impact is unobserved.

Therefore none of those historical aggregate facts may be used as pristine internal Discovery evidence. They are benchmark/context only.

## 4. Core research question

After DEX execution costs, Ethereum base fee, priority fee / direct builder payment, CEX trading cost, hedge slippage / price impact, inventory latency risk and inclusion competition, does a **non-integrated searcher** retain a positive, repeatable net economic margin?

## 5. Frozen hypotheses

### H1 — Existence
For eligible CEX-DEX stale-price events, post-cost realizable net PnL for a non-integrated searcher is positive in aggregate.

### H2 — Robustness
Positive economics are not dependent on one token, one day, one searcher label, one builder, one extreme event or one retrospective execution horizon.

### H3 — Accessibility
At least one frozen notional bucket compatible with a small independent participant remains positive after the full cost stack and a conservative latency/inclusion stress.

## 6. Required cost stack

No result may be called economic edge without all applicable layers:
1. DEX swap fee / pool fee.
2. Ethereum base fee.
3. Priority fee.
4. Direct builder / fee-recipient transfer.
5. CEX taker fee under an explicitly frozen public/default fee assumption unless account-specific verified fees are separately authorized.
6. CEX hedge spread/slippage.
7. Hedge market impact where measurable.
8. Inventory risk for hedge delay.
9. Failed/included transaction treatment.
10. Capital/inventory constraints.

A result that omits a required layer is DESCRIPTIVE_ONLY.

## 7. Data authority ladder

1. On-chain Ethereum transaction/swap data with reproducible transaction hashes.
2. Public curated Fei Wu / Danning Sui CEX-DEX corpus for source feasibility and benchmark replication.
3. MEV-Boost / relay / builder-payment public data where reproducible.
4. CEX market data with point-in-time bid/ask or trade reconstruction and explicit provenance.

Current public one-day sample is **SOURCE FEASIBILITY ONLY**. It cannot adjudicate H1-H3.

## 8. Discovery split

Because the published 2023-08-08 to 2025-03-08 period is contaminated by already-seen external results, it cannot serve as pristine internal Discovery.

Preferred independent evidence order:
- genuinely post-publication / post-freeze data;
- otherwise a prospectively frozen disjoint corpus not used to choose this mechanism.

No 2026 historical backfill may be quietly labeled forward evidence.

## 9. Frozen classifications

Allowed:
- SOURCE_DATA_PASS
- SOURCE_BLOCKED
- DESCRIPTIVE_ONLY
- INSUFFICIENT_SAMPLE
- NO_EDGE
- SURVIVES_DISCOVERY
- REPLICATION_REQUIRED

Forbidden at source gate:
- CANDIDATE
- TIER 2
- QUASE DIAMANTE
- DIAMOND

## 10. Death conditions

The exact MVE dies if, after a valid full-cost execution study:
- net expectancy is non-positive under base costs; or
- stress costs make the mechanism non-viable and base economics are too thin to support a realistic accessible implementation; or
- positive aggregate economics are dominated by a single token/searcher/builder/time bucket; or
- no independent non-integrated access path survives the inclusion/latency model.

No token/timeframe/threshold/venue/direction rescue under the same LAB_ID.

## 11. Current authorized action

Run public source feasibility only. Do not open internal economic outcomes until a complete reproducible dataset and full-cost model are bound. No live trading, transaction submission, wallet mutation, paid-data purchase, protected holdout opening or main merge is authorized by this freeze.
