# BINANCE-DUAL-PRECURSOR-SPOT-HAZARD-003 — V0.1.4 SPOT OUTCOME / CONTROL IMPLEMENTATION FREEZE
Date: 2026-10-06
Status: FROZEN AFTER ALPHA/FUTURES SOURCE UNIVERSE, BEFORE SPOT OUTCOME CLASSIFICATION

## Immutable source universe
Authority: V013_FROZEN_ALPHA_FUTURES_SOURCE_UNIVERSE_2026-10-06.json
- 425 Alpha identity rows with 2025 listingTime
- 406 unique Alpha tickers
- 9 ambiguous Alpha tickers excluded from exact ticker-only DUAL joining
- 193 official Binance Futures launch symbols through 2025
- 98 outcome-blind exact DUAL source candidates with T_DUAL_SOURCE in 2025
- no Spot outcome was opened to construct this universe

## Spot outcome source
Official public Binance CMS only.
Use catalog/category route 48 already source-proven by the Alpha/Futures census.

A Spot-listing announcement qualifies only when the official article title is a Binance Spot listing announcement of the form Binance Will List ... and is not a Futures, Margin, Convert, Earn, HODLer, Alpha-only, delisting, token-swap, rebrand or trading-pair-removal notice.

For a unique Alpha ticker, the first qualifying official Binance Spot listing announcement timestamp in or before 2025 is SPOT_FIRST.
Identity requires exact ticker plus project/name support from the official article when the ticker is not self-disambiguating. Any unresolved identity is SOURCE_AMBIGUOUS and excluded; no guessing.

## DUAL cohort
For each frozen DUAL source candidate:
- T_DUAL = frozen T_DUAL_SOURCE;
- if SPOT_FIRST <= T_DUAL, exclude as ALREADY_SPOT_AT_DUAL;
- otherwise retain as eligible DUAL baseline;
- primary outcome = 1 iff 0 < SPOT_FIRST - T_DUAL <= 7*24h;
- 30d and 90d use the same strict-positive rule and are secondary.

## 2026 outcome firewall
No 2026 Spot listing announcement can be used in V0.1.
For any boundary whose endpoint exceeds 2025-12-31T23:59:59.999Z:
- that horizon is RIGHT_CENSORED_2025;
- it is not counted in that horizon denominator;
- do not query a 2026 outcome to resolve it.
Primary 7d gate therefore uses only DUAL and control observations with complete 7d exposure inside 2025.

## Control cohort — one observation per Alpha identity
To avoid duplicated correlated controls, each unique 2025 Alpha identity receives at most one control boundary.

Construct the sorted set of eligible retained DUAL T_DUAL timestamps.
For each unique Alpha token that is not itself in DUAL state at a candidate boundary:
1. choose the earliest retained DUAL boundary B such that Alpha listingTime <= B;
2. require SPOT_FIRST > B or absent through 2025;
3. require its own frozen first-Futures timestamp, if any, to be > B; therefore it is ALPHA_ONLY at B;
4. assign T_CONTROL=B exactly once;
5. primary/secondary Spot outcomes are measured from T_CONTROL with the same horizon and 2025 censoring rules.

This is baseline/intention-to-treat control classification: a control that enters DUAL after T_CONTROL remains in the control cohort for its frozen horizon. No future exposure-based censoring or reclassification is allowed.

## Primary gate
Use the already frozen V0.1 gates unchanged:
- >=12 eligible DUAL primary observations;
- >=24 eligible ALPHA_ONLY control primary observations, or all available if the census proves fewer;
- DUAL 7d Spot-list rate >=25%;
- DUAL 7d rate >=3x ALPHA_ONLY 7d rate;
- absolute 7d rate difference >=15 percentage points;
- leave-one-out DUAL 7d rate >=20%;
- no single T_DUAL calendar month contributes >35% of DUAL 7d successes.

Fisher exact two-sided p-value is report-only; it cannot rescue a failed gate.

## Verdict
If source/identity/census cannot support the frozen cohorts: SOURCE_BLOCKED.
If any primary gate fails: NO_PREDICTIVE_EDGE_DISCOVERY.
If all pass: SURVIVES_PREDICTIVE_DISCOVERY.

## Market layer
Do not open external-market returns unless and until the predictive gate has been adjudicated.
Market returns cannot rescue a failed predictive gate.

## Governance
2026 validation remains CLOSED.
No live trading, orders, accounts, wallets, private/authenticated endpoints, exchange mutation, main merge or post-outcome tuning.
