# CRYPTO-INDEX-REBALANCE-FLOW-001 — FINAL PRE-DISCOVERY AUTHORITY V0.1

Date: 2026-09-27
Status: FROZEN_PRE_OUTCOME / DISCOVERY_AUTHORIZED_ONCE
Branch: crypto-index-rebalance-flow-v0.1
Draft PR: #144

## Upstream immutable inputs
Source census run: 36329364861
Source census artifact: 10935615452
Source census ZIP SHA256: b3c5911e854e3d915a3a8293c1c7f4c4dccca37e8e4af0d7d52f6516cdc765b0

Event normalization run: 36329760208
Event normalization artifact: 10935685669
Stable event-set SHA256: fffaa5aab3ba17456358af230c3aeda10a74ba55078b6c98b3d1585916db5a17

Binance source coverage run: 36330006396
Coverage artifact: 10935551728
Coverage ZIP SHA256: 0b3c016585f3c445dfa455d1df3e9aeae95359646da13177a5c73a7ff465a2f5
Stable source-eligibility set SHA256: 0d4b35b68a1a119c91db45b5454d6856afc79b6e7e6018304d7b66030ccc723c

## Scientific hypothesis
Scheduled Bitwise benchmark reconstitutions create signed inventory pressure near implementation because benchmark-tracking capital prioritizes tracking error over execution price.

Frozen two-stage fingerprint:

1. Pre-implementation pressure
ADD assets should outperform BTC and REMOVE assets should underperform BTC from T-24h to T0.

2. Post-implementation normalization
After T0, the signed relative effect should reverse from T0 to T+24h.

This is a mechanism Discovery, not yet a trading strategy.

## Discovery window
2022-01-01 through 2024-12-31 only.

2025 = untouched market-data holdout.
2026 = separately governed prospective event.
No 2025 or 2026 market-data URLs may be requested.

## Event universe
Use exactly the 68 source-eligible event legs from SOURCE_COVERAGE_PASS.

Frozen exclusion:
2024-09-29 MATIC REMOVE, because exact MATICUSDT source archives are absent.

No other asset/date/direction may be removed based on outcomes.

## Market source
Official Binance Spot public-data daily 1m klines:
{TICKER}USDT and BTCUSDT.

Every ZIP must be verified against its official .CHECKSUM before parsing.

No API fallback.
No alternate venue.
No alias substitution.
No nearest timestamp.

## T0
For each official Bitwise rebalance date:
16:00:00 America/New_York, converted causally to UTC using the historical timezone database.

Boundaries:
- T-24h
- T0
- T+24h

Boundary price = OPEN of the exact 1-minute kline whose open timestamp equals the boundary.

Missing exact boundary => that event leg is DATA_BOUNDARY_INELIGIBLE.
No fill or interpolation.

## Primary event-leg observables
asset_pre = ln(P_asset(T0) / P_asset(T-24h))
btc_pre   = ln(P_BTC(T0)   / P_BTC(T-24h))

asset_post = ln(P_asset(T+24h) / P_asset(T0))
btc_post   = ln(P_BTC(T+24h)   / P_BTC(T0))

sign = +1 for ADD, -1 for REMOVE.

signed_pre_bps  = sign * (asset_pre  - btc_pre)  * 10,000
signed_post_bps = sign * (asset_post - btc_post) * 10,000

## Statistical unit
Primary inference unit = unique rebalance date.

For each date, equally average all eligible event-leg signed_pre_bps values into date_pre_bps and all signed_post_bps values into date_post_bps.

This prevents overlapping index constituents on the same rebalance from being treated as independent observations.

## Frozen sample gates after exact-boundary parsing
Required before inference:
- >= 50 valid event legs;
- >= 20 distinct rebalance dates;
- all 3 years 2022/2023/2024;
- >= 5 distinct dates per year;
- both ADD and REMOVE represented.

If not met: DISCOVERY_BLOCKED_DATA_INTEGRITY. No scientific verdict.

## Primary inference
Bootstrap the rebalance-date rows with replacement:
- repetitions = 10,000
- seed = 230911
- statistic = mean of date-level means
- two-sided 95% percentile interval

No alternative bootstrap, window or unit after outcomes.

## Mandatory scientific promotion gates
ALL must pass:

A. mean(date_pre_bps) >= +20 bps.
B. bootstrap 95% lower bound for mean(date_pre_bps) > 0.
C. mean(date_post_bps) <= -20 bps.
D. bootstrap 95% upper bound for mean(date_post_bps) < 0.
E. temporal sign stability: at least 2 of 3 calendar-year means have pre > 0 AND post < 0.
F. leave-one-rebalance-date-out joint sign stability >= 80%.
G. max absolute date contribution / sum absolute date contributions <= 25% separately for pre and post.

The 20 bps floor is a pre-outcome materiality screen. This Discovery does not call that amount executable PnL.

## Diagnostics — never rescue gates
Report:
- event-leg ADD/REMOVE means;
- median date effects;
- date hit rates;
- yearly means;
- all leave-one-date-out values;
- raw boundary sample exclusions.

Diagnostics cannot replace any failed mandatory gate.

## Adjudication
If all mandatory gates pass:
DISCOVERY_MECHANISM_PASS_CANDIDATE.

This does NOT authorize Tier 2, live trading, a trading strategy, or opening 2025 automatically.

If any mandatory scientific gate fails:
DISCOVERY_FAIL_NO_PROMOTION.

The exact 24h benchmark-pressure -> normalization mechanism is then closed against horizon/threshold/direction/subperiod/cost rescue.

## Hard firewall
No PnL.
No transaction-cost tuning.
No 2025/2026 market data.
No live trading.
No exchange mutation.
No main merge.
