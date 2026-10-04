# MEXC-HL-WTI-LEADLAG-001 — V1.7 SOURCE COVERAGE CLOSEOUT

Date: 2026-10-04
Run: 37202572039
Rule SHA256: `ec0abf0f23fc96ac417ac979ed2a42199aa0052c4be9625112ebf3ac712abb17`

## Frozen source status

Binding:
`HYPERLIQUID_WTI_SOURCE_PASS__XYZ_CL`

Frozen science:
- FOLLOW_HL_UNDERREACTION
- shock thresholds 5/10/20/40 bps
- lag-gap thresholds 2/5/10/20 bps
- horizons 1/2/5/15m
- next-minute-open entry
- Discovery N>=50 + thirds + Holm
- OOS N>=20 + p<0.05 + halves

## Coverage result

Runner failed closed BEFORE scoring.

MEXC one-minute rows:
35,101

Hyperliquid `xyz:CL` one-minute rows:
4,845

Exact overlap:
4,845

Alignment on available Hyperliquid rows:
1.000

First exact overlap:
`2026-10-01T00:15:00Z`

Last exact overlap before hard boundary:
`2026-10-04T08:59:00Z`

Frozen September Discovery overlap:
0

Frozen October OOS overlap:
4,845

The runner emitted:
`SCORING_NOT_YET_STARTED=true`
then failed:
`DISCOVERY_COVERAGE_INSUFFICIENT:0`

## Verdict

`SOURCE_BLOCKED_HL_WTI_HISTORICAL_RETENTION__NO_SCORING`

This is NOT a NO_EDGE verdict.

## Legitimate successor

Because no return, win rate, p-value or cell score was computed, a source-boundary-only successor may:
- preserve the exact venue binding;
- preserve all thresholds;
- preserve FOLLOW_HL;
- preserve next-minute-open entry;
- preserve horizons;
- preserve Discovery/Holm/OOS gates;
- move the historical windows only to the source-valid period beginning 2026-10-01T00:15:00Z.

No parameter rescue occurred.

No live trading, accounts, private endpoints, wallets, orders, mutation, or main merge.
