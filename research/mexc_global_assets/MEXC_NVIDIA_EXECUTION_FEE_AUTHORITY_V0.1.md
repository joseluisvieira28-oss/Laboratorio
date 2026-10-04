# MEXC NVIDIA EXECUTION FEE AUTHORITY — PUBLIC ROUTE V0.1

Date: 2026-10-04
Status: PUBLIC-AUTHORITY EXECUTION FEASIBILITY ASSESSMENT
Trading authorization: NONE

## Candidate assessed

Discovery survivor:
`MEXC-NVIDIA-REGSESSION-LEADLAG-001`

Frozen winning cell:
- shock >= 5 bps
- lag gap >= 3 bps
- horizon 1 minute
- FOLLOW_EXTERNAL_CONSENSUS
- N=92
- win rate=69.5652%
- mean gross=+3.758750 bps
- median gross=+4.297843 bps

## MEXC public contract metadata

The 2026-10-04 source receipt for `NVIDIA_USDT` reports:
- apiAllowed = true
- isZeroFeeSymbol = true
- makerFeeRate = 0
- takerFeeRate = 0
- maxLeverage = 200

These symbol/UI fields are NOT treated as authenticated API fee authority.

## API fee authority

MEXC official announcement:
`Updates to API Futures Trading Fees (Jun 1, 2026)`
published 2026-05-28 and effective 2026-06-01 08:00 UTC.

Official stated API Futures rates:
- maker = 0.06% = 6 bps per side
- taker = 0.08% = 8 bps per side

The same authority states that the separate API fee structure takes precedence over promotional or zero-fee rates shown on the MEXC website/app.

It states applicability to all Futures trading pairs except Innovation Zone pairs.

Public source:
https://www.mexc.com/announcements/article/updates-to-api-futures-trading-fees-jun-1-2026-17827791535742

## Round-trip fee floor under standard API authority

Fee-only scenarios:
- maker -> maker: 12 bps
- maker -> taker: 14 bps
- taker -> taker: 16 bps

Compared with discovery mean gross:
- gross edge: +3.758750 bps
- after 12 bps fee-only: -8.241250 bps
- after 14 bps fee-only: -10.241250 bps
- after 16 bps fee-only: -12.241250 bps

This excludes spread, slippage, latency, adverse selection and funding.

## Public zero-fee promotion

MEXC announced on 2026-03-06 that NVDA/MRVL Stock Futures supported 24/7 trading and a zero-fee offer for a limited time.

That web/app promotion does not override the later explicit API fee authority.

Public source:
https://www.mexc.com/announcements/article/stock-futures-upgrade-17827791534091

## Current classification

`EXECUTION_FEE_BLOCKED_STANDARD_MEXC_API`

Scientific discovery survival is preserved.

This classification does not prove that every possible execution route is uneconomic. It proves that the standard official MEXC Futures API route, under the current public fee authority, cannot economically support a +3.758750 bps mean gross one-minute signal before other execution costs.

Any claimed fee exception for NVIDIA API must have explicit pair-specific API authority newer than the Jun 1, 2026 API fee schedule before changing this classification.

No authenticated account read, order, wallet operation, private endpoint or live trade was used.
