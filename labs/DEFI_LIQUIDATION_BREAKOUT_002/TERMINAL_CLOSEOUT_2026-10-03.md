# DEFI-LIQUIDATION-BREAKOUT-002 — TERMINAL DEVELOPMENT CLOSEOUT V0.1

Date: 2026-10-03
Classification: **NO_EDGE_DEVELOPMENT_BREAKOUT**

Run: 37135529143
Artifact: 11278318042
Artifact SHA256: a48851746807ce6be578a18d40e9e7417605cdef00d474d52650dae91561e487

Frozen rule:
- same SOL-collateral liquidation cascades as DLS
- observe first complete minute after T0 availability
- sign of that minute chooses LONG/SHORT
- enter one minute later
- exit at E0+5m, four-minute hold
- primary cost 26 bps / stress 40 bps
- no confirmation threshold
- serialized non-overlap

Development 2021-2025:
- source clusters: 21,041
- market complete: 21,041 / 100%
- zero-confirmation no-trades: 552
- candidates: 20,489
- overlap-suppressed: 6,644
- serialized trades: 13,845
- LONG 7,037 / SHORT 6,808
- UTC trade days: 884
- mean gross: -0.002307% (~ -0.231 bps)
- mean primary-net 26 bps: -0.262307% (~ -26.231 bps)
- mean stress-net 40 bps: -0.402307% (~ -40.231 bps)
- primary PF: 0.20268
- day-block bootstrap95 primary net: [-0.269742%, -0.254281%]

Year primary-net means:
- 2021: -0.258728% (N=113)
- 2022: -0.265887% (N=1,888)
- 2023: -0.270606% (N=1,810)
- 2024: -0.260616% (N=6,630)
- 2025: -0.259322% (N=3,404)

Protocol primary-net means:
- Kamino: -0.274333% (N=2,235)
- Marginfi: -0.258050% (N=7,223)
- Save0c: -0.265483% (N=2,001)
- Save11: -0.261266% (N=2,386)

Sample, coverage, year representation and concentration gates passed.
All economic, bootstrap, profit-factor, year-consistency and protocol-family edge gates failed.

The result falsifies the frozen one-minute-confirmation continuation translation.
It does not invalidate the parent direction-agnostic liquidation-volatility effect.

2026 remains completely SEALED for this lab and may not be opened because development failed.

No inversion, horizon change, threshold, side subset, protocol subset, fee reduction or 2026 rescue is permitted under this identity.

Trading authority: NONE.
