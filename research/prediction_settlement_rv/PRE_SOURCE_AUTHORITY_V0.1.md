# PREDICTION-SETTLEMENT-RV-001 — PRE-SOURCE AUTHORITY V0.1

Date: 2026-09-27
Status: FROZEN_PRE_SOURCE / OUTCOME_BLIND / RESEARCH_ONLY
Branch: prediction-settlement-rv-v0.1

## 1. Research question

Can BTC binary contracts with the same resolution instant and displayed nominal strike, but explicitly different settlement functions, exhibit a reproducible executable relative-value basis after realistic fees, depth, synchronization and settlement-risk accounting?

This is NOT a claim that an edge exists.

## 2. Frozen candidate geometry

Polymarket leg:
- BTC threshold event;
- exact resolution instant from market metadata;
- displayed nominal strike K;
- YES when Binance BTC/USDT 1-hour candle Close is strictly greater than K;
- public CLOB token order books.

Kalshi leg:
- KXBTCD threshold event;
- exact same resolution instant;
- displayed nominal strike K;
- encoded threshold K - $0.01 where proven directly in ticker/rules;
- settlement reference CF Benchmarks BRTI;
- public orderbook_fp YES/NO depth.

Primary source class:
MATCHED_SETTLEMENT_BASIS_PAIR

Required properties:
- same UTC resolution instant;
- same displayed nominal strike K;
- both rule sets captured and hashable;
- Polymarket reference = Binance BTC/USDT 1h Close;
- Kalshi reference = CF Benchmarks BRTI;
- exact Kalshi cent-boundary mapping preserved;
- public machine-readable book schemas available on both venues.

The class is intentionally NOT called EXACT_EXCEPT_ORACLE.

## 3. Mechanism statement

Participants may compare the two contracts as nearly fungible claims even though their terminal state maps differ.

Potential basis sources:
- Binance BTC/USDT versus multi-venue USD BRTI;
- the explicit one-cent threshold boundary;
- venue fragmentation and collateral segregation;
- asymmetric depth/spread;
- different fee schedules;
- asynchronous quote updates.

Potential payer:
participants who underprice settlement-definition basis or who pay for immediacy on one venue while the other venue reprices more slowly.

## 4. Failure mode

The hypothesis is invalid or economically unusable if:
- package prices fully compensate for settlement-definition disagreement risk;
- fees/spreads/slippage dominate;
- matched contracts lack usable depth;
- synchronization cannot be maintained;
- one-leg execution risk dominates;
- source semantics change;
- the relation is not stable across genuinely prospective time blocks.

## 5. Current authorized phase

SOURCE/DATA FEASIBILITY ONLY.

Allowed:
- public metadata/rules;
- identifiers;
- timestamps;
- current public bid/ask/depth;
- fee-source discovery;
- source coverage/missingness;
- public USDT/USD source feasibility;
- deterministic matching;
- source hashes/receipts;
- prospective raw capture with values sealed from economic analysis.

Forbidden:
- PnL;
- expectancy;
- win rate;
- package-profit calculation;
- best strike/hour/direction;
- threshold optimization;
- matured outcome analysis;
- live orders;
- authenticated trading endpoints;
- capital;
- exchange mutation;
- merge to main.

## 6. Source gate requirements before economics

All must pass prospectively:
1. deterministic same-time/same-nominal-strike matching;
2. settlement-rule provenance on both legs;
3. explicit cent-boundary preservation;
4. public order-book schema + price + size route on both venues;
5. fee schedule provenance for both venues;
6. one frozen public USDT/USD basis source;
7. synchronized capture tolerance frozen before economic values are opened;
8. stale-quote and schema-change guards;
9. source manifest + SHA256 receipts;
10. zero future-nearest joins;
11. zero silent imputation;
12. prospective source schedule coverage >=99% over a later predeclared gate window.

Until all are satisfied:
SOURCE_DATA_PASS = false.

## 7. Contamination rule

Sibling branch prediction-oracle-basis-v0.1 may be used only as source-engineering evidence.

Its quote values, matured outcomes and any later economics may not be used to select economic rules for this lab.

The new lab must rerun its own source gate under this frozen authority.

## 8. Later economic protocol

NOT YET AUTHORIZED.

After SOURCE_DATA_PASS, a separate pre-outcome protocol must freeze:
- exact package payoff mapping;
- executable ask/bid construction;
- fee formulas;
- fixed observation times;
- sample unit and minimum sample;
- capacity rule;
- settlement disagreement treatment;
- inference;
- shifted-timestamp placebo;
- midpoint diagnostic;
- fee/spread stress;
- one-leg-fill stress;
- leave-time-block-out stability.

## 9. Promotion boundary

Source feasibility is not Tier 3, Tier 2, near-diamond or diamond evidence.

Any later candidate remains subject to the existing Diamond Test and independent prospective evidence.
