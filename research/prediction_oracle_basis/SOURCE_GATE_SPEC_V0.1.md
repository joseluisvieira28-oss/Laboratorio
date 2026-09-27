# PREDICTION-ORACLE-BASIS-001 — SOURCE GATE SPEC V0.1

Status: SOURCE_ROUTE_PARTIAL_PASS / EXACT_MATCH_POPULATION_UNPROVEN / NO ECONOMIC OUTCOMES
Date: 2026-09-27

## Source feasibility established at documentation level

### Polymarket — PASS
Public BTC Up/Down hourly markets explicitly state:
- resolution compares close >= open for the specified 1-hour candle;
- resolution source is Binance;
- exact pair is BTC/USDT;
- the market explicitly warns that it is about Binance BTC/USDT, not another exchange or pair.

This establishes a venue-specific BTC/USDT settlement primitive.

### Kalshi crypto reference — PASS
Kalshi's current crypto-market documentation states:
- crypto price contracts settle from the relevant CF Benchmarks Real-Time Index;
- the settlement value is the average of 60 one-second RTI observations during the final minute before expiration;
- CF Benchmarks RTI is an aggregated price from major exchanges;
- Kalshi makes the CF Benchmarks RTI available through its API as a direct pass-through.

This establishes a distinct institutional BTC/USD-style reference primitive rather than Binance BTC/USDT.

### Executable order-book route — PARTIAL PASS
Kalshi documents public exchange market data and order books with resting price and quantity.
Polymarket visibly operates an order book for BTC Up/Down hourly markets.

A machine-verifiable synchronized bid/ask+size acquisition path on BOTH venues must still be proven by the executable Source Gate before SOURCE_DATA_PASS.

## Critical matching issue
The primary lab requires contracts that are semantically equivalent except for the oracle/reference-price definition.

That equivalence is NOT yet proven.

Polymarket hourly BTC Up/Down compares the hour's Binance BTC/USDT CLOSE versus OPEN.
Kalshi offers multiple crypto price contract forms and uses CF Benchmarks settlement methodology.

The Source Gate must NOT assume that a Kalshi contract is equivalent merely because it is about BTC over a similar time interval.

Required primary classification remains:
- EXACT_EXCEPT_ORACLE
- NON_EQUIVALENT_TIME
- NON_EQUIVALENT_THRESHOLD
- NON_EQUIVALENT_TIE_RULE
- NON_EQUIVALENT_PAYOFF
- NON_EQUIVALENT_OTHER

Only EXACT_EXCEPT_ORACLE may enter a future primary economic test.

## Gate tasks
1. Enumerate current BTC binary series on both venues without selecting by price/PnL.
2. Snapshot exact rule text and immutable identifiers.
3. Determine whether an EXACT_EXCEPT_ORACLE matching population currently exists.
4. Verify machine-readable synchronized executable bid/ask and size collection on both venues.
5. Verify public fee schedule provenance.
6. Capture the exact CF Benchmarks index/reference specified by every candidate Kalshi BTC contract.
7. Freeze one point-in-time USDT/USD basis source before any economic test.
8. Run a source-only prospective capture window.
9. Produce coverage, missingness, timestamp-lag and schema-change diagnostics only.
10. Preserve raw source manifests and hashes.

## Hard stops
If no current EXACT_EXCEPT_ORACLE population exists:
SOURCE_POPULATION_UNAVAILABLE.

Do not broaden to semantically different contracts to manufacture sample size.

If synchronized executable quotes cannot be established:
SOURCE_DATA_BLOCKED.

Do not substitute:
- last trade;
- midpoint;
- screenshots;
- nearest-future quote;
- stale quote;
- reconstructed executable price.

## Adversarial source controls required before economics
- exact timestamp comparison across feeds;
- stale-quote detection;
- intentionally shifted timestamp placebo capability;
- schema-change detector;
- rule-text hash;
- market-identity hash;
- future-nearest join count = 0;
- silent imputation count = 0.

## No economic outputs in Source Gate
Do not calculate:
- strategy PnL;
- profitability;
- win rate;
- optimal threshold;
- best hour;
- best direction;
- expected return;
- oracle-basis performance conditional on market prices.

Those require a separately frozen post-source protocol.
