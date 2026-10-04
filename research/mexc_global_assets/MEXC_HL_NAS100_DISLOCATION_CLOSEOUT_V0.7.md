# MEXC-HL-NAS100-DISLOCATION-001 — V0.7 CLOSEOUT

Date: 2026-10-04
Run: 37195112899
Artifact SHA256: `6bc58c7dfcea4e55d10a22c5dfad0c5714c675665c57a49fbc0d26193e10ca74`

## Provenance

- rule SHA256: `031ba99685af89294eaf1b7b2ebc98b8369e9f1e21020f9129bee641e013d0a3`
- binding SHA256: `1cd51e873faf39d91a665d23868d8bf5859864aecc95d40c7fd05f102eb386ea`
- source alignment: 4,860 / 4,860 exact one-minute rows
- calendar coverage: 100%
- first overlap: 2026-10-01T00:00:00Z
- last overlap: 2026-10-04T08:59:00Z

## Frozen result

Signal family:
`FADE_LEVEL_DISLOCATION`

Frozen thresholds:
10 / 20 / 40 / 80 bps

Frozen horizons:
1 / 2 / 5 / 15 minutes

Frozen execution proxy:
1-minute delay after the closed signal minute.

Discovery result:
- all 16 cells: N = 0
- pre-Holm eligible cells: 0
- Holm-selected cells: 0
- retrospective OOS opened: NO

Verdict:
`NO_NAS100_CROSSVENUE_OOS_SURVIVOR_AT_FROZEN_V07_GATE`

## Interpretation

During the frozen Discovery window, the contemporaneous MEXC NAS100 contract close and Hyperliquid `xyz:XYZ100` close never separated by even the lowest frozen threshold of 10 bps.

Therefore there was no level-dislocation event large enough to enter this family.

This is stronger than a statistical failure: the candidate mechanism had zero trigger opportunities at the minimum economically relevant threshold.

Do not lower the threshold after seeing this result.

## Economic conclusion

The standard MEXC API fee-only hurdle is roughly 12–16 bps round-trip.

A family that generated zero events at 10 bps does not currently justify further same-family tuning for standard API execution.

V0.7 is CLOSED.

No account reads, wallets, private endpoints, orders, exchange mutation or live trading.
