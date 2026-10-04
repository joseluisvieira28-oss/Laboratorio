# MEXC NVIDIA AUTOMATED EXECUTION ROUTE SURVEY V0.1

Date: 2026-10-04
Scope: PUBLIC SOURCES ONLY
Trading authorization: NONE

## Scientific candidate

`MEXC-NVIDIA-REGSESSION-LEADLAG-001`

Discovery survivor:
- shock 5 bps
- lag gap 3 bps
- horizon 1m
- FOLLOW_EXTERNAL_CONSENSUS
- mean gross +3.758750 bps

## Route 1 — Direct MEXC Futures API

Official current public authority effective 2026-06-01:
- maker 0.06% per side
- taker 0.08% per side
- API fee schedule supersedes web/app zero-fee promotions
- applicable to all Futures pairs except Innovation Zone

Classification:
`FEE_BLOCKED`

Fee-only round trip is 12–16 bps versus +3.758750 bps mean gross.

## Route 2 — TradingView / webhook bridge to MEXC

Public MEXC-hosted educational material describes TradingView alerts being translated by a connector and sent to MEXC Futures execution through the exchange API.

This is not evidence of a non-API fee route.

Classification:
`NO_FEE_BYPASS_PROVEN`

## Route 3 — MEXC AI Strategy on web/app

MEXC publicly documents AI Strategy on web/app with strategy types including:
- time
- price
- candlestick patterns
- technical indicators
- social-media monitoring

No public authority inspected on 2026-10-04 proves that AI Strategy can ingest and execute the exact frozen external multi-venue condition:
`mean(Binance NVDAUSDT 1m return, Bitget NVDAUSDT 1m return)`
with the frozen MEXC lag-gap rule.

Classification:
`SIGNAL_COMPATIBILITY_UNPROVEN`

Do not silently approximate the scientific rule with an internal MEXC-only indicator.

## Route 4 — Manual web/app execution

Public contract metadata currently reports NVIDIA_USDT as zero-fee, and the March stock-futures announcement described a zero-fee promotion for a limited time.

Manual execution is not the required autonomous execution model and cannot guarantee the one-minute frozen signal response.

Classification:
`NOT_AN_AUTOMATED_ROUTE`

## Current execution verdict

`NO_PROVEN_AUTOMATED_EXECUTION_ROUTE_WITH_COST_BELOW_DISCOVERY_EDGE`

This does not invalidate the scientific discovery survivor.

Forward validation V0.6 proceeds independently.

Any future route promotion requires explicit authority proving BOTH:
1. it can execute the exact frozen external multi-venue signal automatically; and
2. its all-in expected round-trip cost is below the validated edge.

No order, account read, private endpoint, wallet action or exchange mutation was used.
