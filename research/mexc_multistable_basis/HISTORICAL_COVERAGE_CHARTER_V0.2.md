# MEXC-MULTI-STABLE-BASIS-001 — HISTORICAL COVERAGE PROBE CHARTER V0.2

Date: 2026-10-07
Status: SOURCE-ONLY / OUTCOME-BLIND
Parent: SOURCE_GATE_CLOSEOUT_V0.1.md = SOURCE_PASS

Purpose:
Determine whether the six frozen candidate perpetual contracts and stablecoin-normalization spot routes expose historical 1-minute data across a predeclared set of calendar anchors. This is a transport/coverage test only.

Frozen candidate contracts:
- BTC_USDT
- BTC_USDC
- BTC_USD1
- ETH_USDT
- ETH_USDC
- ETH_USD1

Frozen normalization routes:
- USDCUSDT
- USD1USDT
- USD1USDC (consistency only)

Frozen UTC anchor windows:
- 2026-05-01 00:00–01:00
- 2026-06-01 00:00–01:00
- 2026-07-01 00:00–01:00
- 2026-08-01 00:00–01:00
- 2026-09-01 00:00–01:00
- 2026-10-01 00:00–01:00

For each route/window record ONLY:
- HTTP/source success
- number of 1-minute rows
- number of unique timestamps
- expected timestamp count
- exact first/last timestamps when present
- response SHA-256 and latency

Forbidden:
- reading/reporting OHLC values
- cross-contract basis
- returns
- lead/lag
- convergence
- funding economics
- PnL
- threshold/horizon search

Anchor PASS requires 60/60 exact minute timestamps for every required route in that anchor window.

Probe verdict:
- COVERAGE_ANCHOR_PASS if every required route passes every frozen anchor
- COVERAGE_PARTIAL if at least one anchor/route fails while current source remains available
- SOURCE_BLOCKED if historical route semantics are not defensibly usable

This probe does not authorize outcomes. Full-sample coverage and a separate immutable pre-outcome freeze remain required before any economic test.
