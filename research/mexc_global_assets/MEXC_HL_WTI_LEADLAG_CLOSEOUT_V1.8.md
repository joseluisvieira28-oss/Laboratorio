# MEXC-HL-WTI-LEADLAG-001 — V1.8 CLOSEOUT

Date: 2026-10-04
Canonical successful run: 37202729248
Artifact SHA256: `a3d7a3c4525b2a57fb0535970b5082d4c73f6c52ce630b0742f8434928b8845a`
Rule SHA256: `535b4b98fd09c94f6f42d158a9c5371e48437d57b1043c6419b20fc208f909cc`

## Coverage

- exact MEXC ↔ Hyperliquid alignment: 1.000
- total exact overlap: 4,845 minutes
- Discovery overlap: 2,865 minutes
- OOS overlap available but not opened: 1,981 minutes
- first overlap: 2026-10-01T00:15:00Z
- last overlap: 2026-10-04T08:59:00Z

## Frozen family

64 cells:
- Hyperliquid shock: 5 / 10 / 20 / 40 bps
- MEXC underreaction gap: 2 / 5 / 10 / 20 bps
- horizons: 1 / 2 / 5 / 15m
- direction: FOLLOW_HL only
- entry: MEXC next-minute open
- Discovery N>=50 + all thirds positive + Holm FWER 0.05

## Scientific result

- pre-Holm eligible cells: 1
- Holm-selected cells: 0
- OOS opened: NO
- OOS survivors: 0

Frozen verdict:
`NO_WTI_CROSSVENUE_OOS_SURVIVOR_AT_FROZEN_V18_GATE`

## Sole pre-Holm eligible cell

HL shock >=5 bps
MEXC underreaction gap >=2 bps
Horizon 1m

- N=255
- wins=132
- losses=123
- win rate=51.7647%
- mean gross=+1.80334 bps
- median gross=+1.08120 bps
- one-sided exact binomial p=0.308236
- thirds:
  - +0.91813 bps
  - +2.77185 bps
  - +1.72005 bps
- Holm cutoff=0.05

Economics:
- 0 bps cost: +1.80334
- 1 bps: +0.80334
- 2 bps: -0.19666
- 3 bps: -1.19666
- 5 bps: -3.19666
- 10 bps: -8.19666

It failed Holm and did not clear the 2 bps current taker/taker fee-only hurdle.

## Strongest descriptive near-cell — NOT eligible

HL shock >=5 bps
MEXC underreaction gap >=5 bps
Horizon 1m

- N=42
- wins=26
- win rate=61.9048%
- mean gross=+3.52498 bps
- p=0.0820747
- thirds:
  - +5.71102 bps
  - +2.32130 bps
  - +2.54264 bps

Illustrative current fee-only economics:
- 0 bps: +3.52498
- 1 bps: +2.52498
- 2 bps: +1.52498
- 3 bps: +0.52498
- 5 bps: -1.47502

This cell failed the frozen minimum N=50 and was not eligible for Holm.

It may not be rescued retrospectively by lowering N.

If ever pursued again, it must be frozen as a new single-cell FUTURE-FORWARD observation before new data arrive.

## Other large-return cells

Some higher shock cells showed double-digit gross means, e.g. >=20 bps shock / >=2 bps gap / 15m at +15.32 bps gross, but sample size was only N=18 and one chronological third was negative.

These are anecdotes, not candidates.

## Final interpretation

The source binding is real and high quality:
MEXC `USOIL_USDT` ↔ Hyperliquid `xyz:CL` / WTI.

However the frozen short-history lead/lag family produced no statistically promotable signal.

Do not:
- lower N;
- add FADE on this historical sample;
- retune thresholds around the N=42 cell;
- open OOS for a failed Discovery family.

V1.8 is CLOSED.

No live trading, account reads, private endpoints, wallets, orders, exchange mutation, or main merge.
