# MEXC-HL-WTI-LEADLAG-001 — SOURCE-VALID PRE-OUTCOME FREEZE V1.8

Date: 2026-10-04
Status: FROZEN BEFORE ANY WTI CROSS-VENUE PERFORMANCE SCORING

## Why V1.8 exists

V1.7 failed closed on source coverage before scoring.

Proven first exact MEXC ↔ Hyperliquid `xyz:CL` one-minute overlap:
`2026-10-01T00:15:00Z`

V1.7 emitted `SCORING_NOT_YET_STARTED=true` and calculated no return, win rate, p-value, Holm selection or OOS result.

V1.8 therefore changes ONLY the historical windows.

## Scientific parameters preserved exactly

- binding: MEXC `USOIL_USDT` ↔ Hyperliquid `xyz:CL`;
- signal: `FOLLOW_HL_UNDERREACTION`;
- Hyperliquid shock thresholds: 5 / 10 / 20 / 40 bps;
- MEXC underreaction gaps: 2 / 5 / 10 / 20 bps;
- horizons: 1 / 2 / 5 / 15 minutes;
- entry: MEXC next-minute open;
- per-cell cooldown through exit;
- Discovery N>=50;
- mean > 0;
- win rate > 50%;
- all chronological thirds > 0;
- Holm-Bonferroni FWER 0.05;
- OOS N>=20;
- OOS exact one-sided binomial p<0.05;
- both OOS half means >=0;
- no FADE;
- no parameter rescue.

## Source-valid windows

Discovery:
`2026-10-01T00:15:00Z <= signal t < 2026-10-03T00:00:00Z`

Retrospective OOS:
`2026-10-03T00:00:00Z <= signal t < 2026-10-04T09:00:00Z`

Hard boundary:
`2026-10-04T09:00:00Z`

These returns were not scored by V1.7.

## Economics

Current MEXC metadata snapshot around this study:
- maker = 0
- taker = 0.0001 per side

Report 0 / 1 / 2 / 3 / 5 / 10 bps round-trip scenarios.

Fee-only hurdles:
1 / 2 / 3 bps.

Spread/slippage remain unmeasured.

## Promotion ceiling

OOS PASS =>
`WTI_CROSSVENUE_OOS_SIGNAL_CANDIDATE`

No live trading, account reads, private endpoints, wallets, orders, exchange mutation, or main merge.
