# LICP-HIST-XALT-003 — HOLDOUT RESULT V0.1

Date: 2026-09-26
Workflow run: 36234052123
Status: HOLDOUT_SURVIVES

## Frozen candidate
- event source: BTC ignition events from the pinned external Hyperliquid event table
- target: SOLUSDT
- direction: SHORT continuation
- primary entry proxy: t0 + 6 minutes
- horizon: 60 minutes
- transfer hurdle: 16 bps
- reversal rescue: prohibited

## Locked holdout
- 2025-11-01 through 2025-12-31 UTC
- single-pass: YES
- Discovery reopened: NO

## Coverage
- eligible BTC ignition events: 35
- valid events: 35
- missing events: 0
- missing rate: 0%

## Pooled holdout
- n = 35
- mean gross directional move = +25.0713922256 bps
- median gross directional move = +16.8823860439 bps
- positive rate = 60.0%
- mean transfer-ceiling net after 16 bps hurdle = +9.0713922256 bps

## By month

### 2025-11
- n = 15
- mean gross = +2.7074814256 bps
- median gross = +23.9144115796 bps
- positive rate = 53.33%
- mean transfer-ceiling net = -13.2925185744 bps

### 2025-12
- n = 20
- mean gross = +41.8443253256 bps
- median gross = +14.3849817627 bps
- positive rate = 65.0%
- mean transfer-ceiling net = +25.8443253256 bps

## Frozen-rule evaluation
PASS criteria:
1. n >= 20 — PASS
2. pooled mean gross > 16 bps — PASS
3. pooled median gross > 0 — PASS
4. November and December means positive when n>=5 — PASS
5. missing-price rate <=10% — PASS

Decision:
HOLDOUT_SURVIVES

## Scientific interpretation
This is a genuine out-of-sample survival of the frozen coarse cross-asset continuation hypothesis:
BTC liquidation ignition -> SOL short continuation over 60 minutes.

It is NOT yet:
- executable MEXC PnL;
- proof of MEXC transferability;
- proof of sub-minute trigger quality;
- proof of live profitability;
- live-trading authority.

The historical source uses Hyperliquid event timing and Binance Vision SOLUSDT 1-minute opens. Current MEXC API fees are represented only by the 16 bps transfer hurdle; spread/slippage/fill quality are not modeled.

## Next gate
Create an independent forward transferability study that preserves:
- BTC liquidation ignition as a causal observable event;
- SOL short continuation direction;
- 60-minute horizon;
- no post-holdout retuning.

The next gate must use target-venue MEXC executable BBOs and a defensible real-time liquidation trigger source.

No historical 2026 data is opened by this result.
