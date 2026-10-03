# OPTIONS-RR-TERM-FWD-001 — SOURCE-ONLY CALIBRATION FREEZE V0.1

Date: 2026-10-03
Status: PRE-OUTCOME / FORWARD SOURCE-ONLY
Parent source freeze: OPTIONS_RR_TERM_SOURCE_GATE_FREEZE_V01.md

## Purpose

Estimate a prospective, outcome-blind rarity threshold for the frozen 25-delta risk-reversal
term-spread:

`rr_term_pp = (putIV25_short - callIV25_short) - (putIV25_medium - callIV25_medium)`

No price future, MEXC payout, MEXC index, Event Futures outcome, return, win/loss or PnL may
enter this calibration.

## Source identity

Exactly preserve the V0.1 source-gate algorithm:

SHORT:
- nearest active expiry in DTE [7,21] days.

MEDIUM:
- nearest active expiry in DTE [35,70] days.

For each expiry:
- OTM call and OTM put;
- actual accepted delta call [+0.15,+0.35], put [-0.35,-0.15];
- closest |delta| to 0.25;
- same ticker validity rules as source gate;
- call/put timestamp spread <=5000 ms.

Across all four selected tickers:
- timestamp spread <=10000 ms.

No fallback outside the bucket.
No interpolation.
No alternative delta target.

## Forward calibration boundary

Only UTC-minute source rounds strictly after the first commit containing this freeze may enter
calibration.

Any source-gate observations are excluded.

## Sampling

- currencies: BTC, ETH;
- one source round per UTC minute;
- no same-minute retry;
- if a minute fails source validation, record it as missing/invalid;
- never impute a missing minute;
- preserve raw response hashes and selected instrument identities.

## Minimum calibration evidence

For EACH currency independently:

- >=1440 unique UTC minutes observed;
- >=1200 valid dual-expiry rr_term observations;
- zero unresolved source-integrity conflicts.

Until both currencies satisfy all minima:
`SOURCE_CALIBRATION_INCOMPLETE`.

## Numeric threshold rule frozen now

For each currency separately:

1. collect `abs(rr_term_pp)` from valid calibration minutes;
2. sort ascending;
3. nearest-rank P95 index = `ceil(0.95*n)`;
4. threshold = value at that rank.

No other quantile is tested.
No return-conditioned calibration.
No direction-specific threshold.
No payout filter.
No volatility/regime filter.
No symbol selection after calibration.

If threshold is nonfinite or <=0 => FAIL_CLOSED.

## Future activation rule — NOT ACTIVE YET

After both currencies satisfy calibration minima, a separate activation freeze must commit
the exact numeric BTC and ETH thresholds and calibration artifact hashes BEFORE the first
outcome.

Frozen future signal:
- rr_term_pp >= +threshold(symbol) => DOWN;
- rr_term_pp <= -threshold(symbol) => UP;
- otherwise NO_SIGNAL.

Direction policy:
`FOLLOW_NEAR_TERM_DOWNSIDE_STRESS`.

Event Futures mapping:
- BTC -> BTC_USDT
- ETH -> ETH_USDT
- horizon = exactly 10 minutes
- source signal age <=5 seconds
- first-only unresolved overlap per symbol
- exact V0.13 contemporaneous direction-specific payout
- no payout filter beyond q>0
- min N = 100 resolved nonblocked events per symbol
- 30-day evaluation batch; no early significance verdict.

## Chunking

Initial calibration is executed in bounded 180-minute chunks.

Chunks may be merged only when:
- minute identities are unique or byte-identical duplicates;
- no conflicting duplicate minute exists;
- no minute precedes the frozen calibration boundary.

No overlapping chunk may be intentionally launched.

## Governance

- no outcomes in calibration;
- no MEXC access in calibration;
- no V0.1 OPTIONS-VOL threshold reuse;
- no ETH skew-shock rescue;
- no post-outcome tuning;
- no live trading/orders;
- no private/account/wallet access;
- no main merge.
