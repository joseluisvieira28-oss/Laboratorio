# BINANCE-LISTING-INFORMATION-CASCADE-001 — V0.3 2025 HOLDOUT PRE-OUTCOME FREEZE
Date: 2026-10-05
Status: FROZEN BEFORE ANY 2025 MARKET OUTCOME ACCESS

## Purpose
Test whether the Binance public-listing announcement information cascade discovered in 2024 replicates in an untouched calendar-year 2025 holdout.

## Event census
Authority: official Binance CMS catalog.
Census rule: every 2025 official article whose title begins exactly with "Binance Will List ".
T0: exact official Binance CMS releaseDate.
Multiple assets named in one announcement remain separate asset observations, matching V0.1/V0.2.
No manual event cherry-picking.

## Exclusions
Same structural exclusions as V0.1/V0.2:
- stablecoins;
- wrapped fiat-like assets;
- staked/wrapped derivatives;
- assets without at least 24h of continuous pre-T0 public spot trading on the selected comparison venue;
- announcements whose exact first-public timestamp cannot be defended.

## Frozen comparison venue hierarchy
Primary hierarchy is fixed BEFORE the 2025 source census and outcomes:
1. Bitget spot
2. KuCoin spot
Only if Bitget has no valid source coverage may KuCoin be used.
No venue shopping after outcomes.
Other venues may be used only for source diagnostics or post-result integrity replication; they cannot replace the primary hierarchy in V0.3.

## Frozen measurements
P0 = close of final complete 1m candle strictly before the T0 minute.
Exact clock-aligned returns:
- R1 = close at T0-minute +1m / P0 - 1
- R5 = close at +5m / P0 - 1
- R15 = close at +15m / P0 - 1
- R60 = close at +60m / P0 - 1
MFE/MAE over the same horizons.
5m volume shock = first 5 wall-clock minutes from T0 / median non-overlapping wall-clock 5m volume buckets from T-24h through T-1h.
Missing no-trade 1m candles count as zero volume only; price target candles must exist exactly.

## Frozen holdout gate
V0.3 SURVIVES_HOLDOUT iff ALL:
- n >= 12 valid observations;
- median R15 > +0.75%;
- R15 positive hit rate >= 65%;
- median R5 > +0.50%;
- median 5m volume shock >= 2x;
- leave-one-out median R15 remains > 0 after dropping any one observation;
- no single observation contributes >35% of summed positive R15.

If n<12: SOURCE_BLOCKED_HOLDOUT.
If n>=12 but any performance gate fails: NO_EDGE_HOLDOUT.
No gate, threshold, direction, unit-of-analysis, inclusion rule, venue priority or horizon may change after any 2025 outcome is opened.

## Governance
2026 remains CLOSED and untouched.
No fees/slippage/latency/execution claim is permitted unless V0.3 survives.
No live trading, accounts, orders, wallets, private endpoints, exchange mutation or main merge.
