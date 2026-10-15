# POB-HOURLY-STRIKE-BINANCE-CFRTI-001 — PRE-SOURCE CHILD AUTHORITY V0.1

Date: 2026-09-27
Parent: PREDICTION-ORACLE-BASIS-001
Status: FROZEN_PRE_SOURCE / OUTCOME_BLIND / RESEARCH_ONLY
Branch: prediction-oracle-basis-v0.1

## Rationale

The daily explicit-strike child proved a valid Polymarket source population but found no current exact resolution-time overlap with the currently open Kalshi KXBTCD population.

That was a source-population timing result, not an economic failure.

This child tests the materially distinct CURRENT HOURLY source population. It is frozen before inspecting any matured outcome or any cross-venue package economics.

## Deterministic source-matching rule

1. Enumerate all current open KXBTCD markets from the public Kalshi API.
2. Extract unique future resolution instants.
3. Keep only instants strictly after probe time and within the next 12 hours.
4. Convert each instant to America/New_York civil time.
5. Construct exactly one Polymarket hourly event slug from that time:
   bitcoin-above-on-<month>-<day>-<year>-<hour><am|pm>-et
6. Query that slug directly from Polymarket Gamma.
7. Match only identical nominal strikes and identical resolution instants.

No quote, market probability, volume, outcome or profitability field may influence which times or strikes are queried.

## Frozen contract classification

For each exact time + nominal strike pair:
- MATCHED_HOURLY_STRIKE_TIME_REFERENCE_DIFF_TIE_1C
- POLY_RULE_PROVENANCE_BLOCKED
- KALSHI_REFERENCE_PROVENANCE_BLOCKED
- NON_EQUIVALENT_STRIKE
- NON_EQUIVALENT_TIME
- NON_EQUIVALENT_OTHER

MATCHED_HOURLY_STRIKE_TIME_REFERENCE_DIFF_TIE_1C requires:
- same BTC underlying;
- same resolution instant;
- same displayed nominal strike;
- Polymarket strict > nominal strike;
- Kalshi threshold encoded one cent below displayed nominal strike;
- Polymarket reference proven as Binance BTC/USDT candle close;
- Kalshi reference proven as CF Benchmarks BRTI;
- public executable order-book routes present on both venues.

This class is NOT labeled EXACT_EXCEPT_ORACLE because the one-cent boundary remains explicit.

## Source phase only

Allowed:
- public metadata/rules;
- identifiers;
- timestamps;
- nominal strikes;
- encoded thresholds;
- quote/depth schema existence;
- source hashes;
- matched-pair counts;
- missingness/timestamp diagnostics.

Forbidden:
- matured outcomes;
- PnL;
- expected return;
- win rate;
- arbitrage-profit calculation;
- best time/strike selection;
- backtest;
- orders;
- authenticated trading;
- capital;
- exchange mutation;
- merge to main.

## Gate

SOURCE_SHAPE_PASS requires at least one matched hourly pair with:
- source-proven rules/reference;
- exact time and nominal strike match;
- Polymarket YES/NO token IDs;
- public Polymarket book route readable;
- public Kalshi order-book route readable;
- zero future-nearest joins;
- zero silent imputation.

A Source Shape PASS authorizes only a later separately frozen prospective synchronized-capture design.
