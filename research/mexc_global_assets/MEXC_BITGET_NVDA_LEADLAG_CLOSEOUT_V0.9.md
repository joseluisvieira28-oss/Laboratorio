# MEXC-BITGET-NVDA-LEADLAG-001 — V0.9 CLOSEOUT

Date: 2026-10-04
Run: 37195769376
Artifact SHA256: `01220e83ac1428cfb7651a955bea0d4a90ef695a782835bb9a2b8008eb7c6a4b`
Rule SHA256: `18983ecbe4ac9e5b26334de6f72b728f25e7486581af9d37f7fecb2fbe77c2d2`

## Source coverage

- exact MEXC/Bitget timestamp alignment: 1.000
- Discovery overlap rows: 21,577
- OOS overlap rows available but unopened: 15,823
- first overlap: 2026-09-05T00:00:00Z
- last overlap: 2026-09-30T23:59:00Z

## Frozen family

64 cells:
- Bitget 1m shocks: 10 / 20 / 40 / 80 bps
- MEXC-underreaction lag gaps: 5 / 10 / 20 / 40 bps
- horizons: 1 / 2 / 5 / 15 minutes
- direction: FOLLOW_BITGET only
- entry proxy: MEXC next-minute open

## Result

- pre-Holm eligible cells: 1
- Holm-selected cells: 0
- OOS opened: NO
- OOS survivors: 0

Frozen verdict:
`NO_NVDA_CROSSVENUE_OOS_SURVIVOR_AT_FROZEN_V09_GATE`

## Sole pre-Holm eligible descriptive cell

- Bitget shock threshold: 10 bps
- lag-gap threshold: 5 bps
- horizon: 2 minutes
- N: 54
- wins: 28
- win rate: 51.8519%
- mean gross: +3.62294 bps
- median gross: +0.44867 bps
- one-sided exact binomial p vs 50%: 0.44596
- chronological third means: +2.6231 / +3.8563 / +4.3894 bps
- longs / shorts: 24 / 30
- mean absolute Bitget shock: 16.2644 bps
- mean absolute lag gap: 8.6082 bps

Holm cutoff for the only eligible cell was 0.05.

Its p-value 0.44596 is far above the cutoff, so the cell did NOT earn OOS access.

## Economics

Illustrative mean net for the descriptive cell:
- 0 bps cost: +3.6229 bps
- 2 bps: +1.6229 bps
- 5 bps: -1.3771 bps
- 10 bps: -6.3771 bps
- 12 bps: -8.3771 bps
- 14 bps: -10.3771 bps
- 16 bps: -12.3771 bps

It cleared none of the 12/14/16 bps standard-MEXC-API fee-only hurdles.

## Interpretation

There is a weak descriptive hint of same-direction catch-up in one low-threshold cell, but it is neither statistically robust nor economically sufficient for the standard API route.

Do not retune V0.9 around this cell.
Do not open its OOS.

V0.9 is CLOSED.

No live trading, account reads, wallets, private endpoints, orders or exchange mutation.
