# MEXC-HL-NAS100-LEADLAG-001 — DISCOVERY CLOSEOUT V0.6

Date: 2026-10-04
Run: 37194281396
Head: `50997400967c977a0dec20eeb5d60ab0ff91b415`

## Provenance

- rule SHA256: `ba4c2df3cd1c343e8e0128dee983de650794ef65107a2b5145c4e2169537be5d`
- binding SHA256: `9d76633fa3393b483e5cb389b1f9c3e77945aabdb65f846fe499b35c3b66ac5c`
- artifact ZIP SHA256: `fb763c37d51e46cfddad887f1ce652abcdac828c2355a40ed255554c2ca9ad16`

Governance:
- discovery only;
- no retrospective OOS;
- no data at or after 2026-10-04T09:00:00Z;
- no parameter rescue;
- no private endpoints/account reads/wallets/orders/mutation;
- no live trading.

## Coverage

Exact 1-minute MEXC↔Hyperliquid clock overlap:
- expected minutes: 4,860
- exact overlap minutes: 4,860
- coverage ratio: 1.000

## Frozen result

64 cells:
- Hyperliquid shock: 5 / 10 / 20 / 40 bps
- lag gap: 3 / 5 / 10 / 20 bps
- horizons: 1 / 2 / 5 / 15m
- direction: FOLLOW_HYPERLIQUID

Result:
- pre-Holm eligible: 0
- Holm-selected: 0
- no retrospective OOS opened.

## Why no promotion

The family was underpowered at the frozen N>=20 gate.

Widest active cell family:
`shock=5 bps / gap=3 bps`

Observed:
- 1m: N=15, win rate=66.67%, mean gross=+1.6314 bps, p=0.150879
- 2m: N=14, win rate=64.29%, mean gross=+2.4854 bps, p=0.211975
- 5m: N=13, win rate=61.54%, mean gross=+0.3901 bps, p=0.290527
- 15m: N=11, win rate=54.55%, mean gross=+2.9774 bps, p=0.500000

At `shock=5 / gap=5`, only 2 events occurred, although the 15m mean gross was +19.9611 bps.

No cell reached N>=20, so no cell could enter the pre-Holm eligibility set.

## Scientific classification

`UNDERPOWERED_NO_PROMOTION_AT_FROZEN_V06_GATE`

Do not lower the frozen N threshold or retune the grid after observing these outcomes.

The signal-like behavior can only be revisited with a new untouched future sample using a pre-frozen continuation rule.

## Next distinct mine

Move to GOLD multi-venue consensus:
MEXC `XAU_USDT` versus the public XAUUSDT perpetual markets used by its index-origin set (Binance / Bitget / Bybit).
