# CRYPTO-INDEX-REBALANCE-FLOW-001 — MEASUREMENT FREEZE V0.2

Date: 2026-09-27
Parent authority: PROSPECTIVE_AUTHORITY_V0.1
Status: FROZEN_PRE_T0 / OBSERVATIONAL / NO TRADING
T0: 2026-09-30T20:00:00Z

## Fixed cohort
ADDS:
- UNIUSDT
- ZECUSDT
- SKYUSDT

REMOVES:
- SUIUSDT
- LTCUSDT
- CRVUSDT

Control:
- BTCUSDT

No asset may be removed after T0 because of performance.
If an exact source asset is unavailable, record SOURCE_ASSET_UNAVAILABLE. Do not substitute another exchange or token mapping in V0.2.

## Primary source
Official Binance Spot public-data daily 1-minute klines from data.binance.vision.

Required UTC dates:
- 2026-09-09 through 2026-09-29 for the pre-event same-clock volume baseline;
- 2026-09-29 for T-24h;
- 2026-09-30 for T0;
- 2026-10-01 for T+24h boundary.

Daily archives must be acquired only from the exact frozen path pattern:
data/spot/daily/klines/{SYMBOL}/1m/{SYMBOL}-1m-{YYYY-MM-DD}.zip

Where an official CHECKSUM sidecar exists, it must verify before parsing.
Archive bytes and normalized input manifest must be SHA256-preserved.

No nearest-day substitution.
No alternative venue fallback inside this MVE.

## Timestamp semantics
Binance Spot public-data timestamps from 2025 onward are microseconds.
The parser must normalize source timestamps to UTC without changing row order.

Boundary price:
- use the OPEN of the exact 1-minute kline whose open timestamp equals the frozen boundary.
- T-24h = 2026-09-29T20:00:00Z.
- T0 = 2026-09-30T20:00:00Z.
- T+24h = 2026-10-01T20:00:00Z.

If an exact boundary candle is absent: MISSING_EXACT_BOUNDARY. No nearest-neighbor fill.

## Frozen observables
For each cohort asset i:

pre_relative_i =
  log(P_i(T0)/P_i(T-24h))
  - log(P_BTC(T0)/P_BTC(T-24h))

post_relative_i =
  log(P_i(T+24h)/P_i(T0))
  - log(P_BTC(T+24h)/P_BTC(T0))

sign_i:
- +1 for ADD
- -1 for REMOVE

signed_pre_i = sign_i * pre_relative_i
signed_post_i = sign_i * post_relative_i

Interpretation fixed before T0:
- benchmark-pressure fingerprint expects signed_pre > 0;
- post-implementation normalization expects signed_post < 0.

These are mechanism observables, NOT trades or PnL.

## Frozen volume fingerprint
Event window = [T0-30m, T0+30m), exactly 60 one-minute bars.

event_quote_volume_i = sum quote_asset_volume over that window.

Baseline uses the exact same UTC clock window [19:30, 20:30) for each of the 20 prior UTC dates:
2026-09-10 through 2026-09-29 inclusive.

baseline_quote_volume_i = median of the 20 daily window sums.

volume_ratio_i = event_quote_volume_i / baseline_quote_volume_i.

No deletion of low/high baseline days.
No announcement-date exclusion.
No alternative baseline after T0.

## Cohort summaries
Primary descriptive summaries:
- mean signed_pre across all six fixed assets;
- median signed_pre;
- mean signed_post;
- median signed_post;
- median volume_ratio.

Mandatory concentration diagnostic:
- leave-one-asset-out mean signed_pre for each of six omissions;
- leave-one-asset-out mean signed_post for each of six omissions.

This single event is a prospective pilot and cannot establish promotion, Tier 2, or a tradable edge regardless of magnitude.

## Optional liquidity diagnostics
Spread/depth are secondary only and may be reported only from a separately frozen reproducible point-in-time source.
They cannot rescue the primary pilot.

## Forbidden
- PnL or trade returns;
- leverage;
- thresholds selected after T0;
- asset deletion;
- alternate T0;
- alternate control;
- alternate baseline;
- nearest timestamp;
- other exchange substitution;
- parameter rescue.

## Adjudication
SOURCE_DATA_BLOCKED if exact required source bytes cannot be acquired.
PILOT_INCOMPLETE if any mandatory boundary cannot be established for the full fixed cohort.
MECHANISM_FINGERPRINT_OBSERVED only describes the predeclared sign pattern; it is not an edge verdict.
MECHANISM_FINGERPRINT_NOT_OBSERVED if the predeclared pattern is absent.
