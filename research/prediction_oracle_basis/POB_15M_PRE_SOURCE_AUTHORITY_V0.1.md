# POB-15M-CHAINLINK-CFRTI-001 — PRE-SOURCE CHILD AUTHORITY V0.1

Date: 2026-09-27
Parent lab: PREDICTION-ORACLE-BASIS-001
Status: FROZEN_PRE_SOURCE / OUTCOME_BLIND / RESEARCH_ONLY
Branch: prediction-oracle-basis-v0.1

## Why this child exists
The parent lab was opened around cross-venue BTC binary settlement geometry. Current public market documentation reveals a materially distinct and potentially cleaner 15-minute pairing than the original BTC/USDT-vs-BTC/USD framing:

- Polymarket current BTC Up/Down 15-minute markets resolve from Chainlink BTC/USD TWAP over the specified interval.
- Kalshi KXBTC15M markets resolve their terminal BTC value from CF Benchmarks BRTI using the final 60 one-second observations.

This is NOT a silent rewrite of the parent stablecoin-basis mechanism. It is a separately identified child mechanism:
CHAINLINK BTC/USD interval reference vs CF BENCHMARKS BRTI reference.

## Primary scientific question
Does a current population exist where the two contracts are equivalent in:
- underlying;
- start/end interval;
- binary direction;
- threshold initialization;
- tie rule;
- settlement timing;
- payoff;

and differ materially only in the reference-price/oracle construction?

Only such a population may be labeled EXACT_EXCEPT_ORACLE.

## Current source-state
SOURCE_SHAPE_MATCH_CANDIDATE / TARGET_INITIALIZATION_UNPROVEN.

Known:
- Polymarket 15m is an interval Up/Down contract.
- Kalshi KXBTC15M is a 15-minute BTC binary contract with a displayed Target Price and terminal CF Benchmarks BRTI settlement value.

Not yet proven:
- the exact rule that generates Kalshi's initial Target Price;
- equivalence of the start reference to Polymarket's start TWAP/reference;
- identical tie semantics;
- exact interval alignment for a live pair.

Therefore NO exact-match claim is authorized yet.

## Required fail-closed equivalence test
For each prospective matched pair, classify:
- EXACT_EXCEPT_ORACLE
- TARGET_INITIALIZATION_UNPROVEN
- NON_EQUIVALENT_TIME
- NON_EQUIVALENT_THRESHOLD
- NON_EQUIVALENT_TIE_RULE
- NON_EQUIVALENT_PAYOFF
- NON_EQUIVALENT_OTHER

The primary mechanism may advance only if official source text/data establishes EXACT_EXCEPT_ORACLE.

Third-party descriptions are discovery aids only and cannot upgrade the classification.

## Source primitives
Polymarket:
- Gamma public market/event metadata;
- exact market rules/description;
- CLOB public order book for YES/NO token IDs;
- Chainlink BTC/USD TWAP public RTDS feed, when prospective capture is later authorized.

Kalshi:
- public GET /markets filtered to KXBTC15M;
- public market rule fields and timestamps;
- public YES/NO bid/ask and displayed sizes;
- series settlement source metadata;
- CF Benchmarks RTI methodology as settlement authority.
- direct BRTI feed only if legitimately accessible under the relevant public/entitled route; no credential guessing.

## Source gate only
Allowed outputs:
- source HTTP status;
- market counts;
- immutable IDs/tickers;
- open/close timestamps;
- rules text hashes;
- order-book schema/quote presence;
- source hashes;
- exact-match classification;
- missingness;
- timestamp diagnostics.

Forbidden:
- PnL;
- expected return;
- win rate;
- best time;
- best direction;
- conditional profitability;
- threshold optimization;
- trade simulation;
- orders/capital/exchange mutation.

## Critical falsifier
If Kalshi's target is not generated from a contemporaneous reference equivalent to the start-side object used by Polymarket, the pair is not EXACT_EXCEPT_ORACLE.

If no exact population exists, close this child as SOURCE_POPULATION_UNAVAILABLE or SOURCE_RULE_PROVENANCE_BLOCKED. Do not broaden the contract definition after seeing market prices.

## Governance
No live trading.
No authenticated trading endpoints.
No protected-outcome opening.
No post-outcome tuning.
No main merge.
