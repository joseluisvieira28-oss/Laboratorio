# MEXC-WTI-EIA-FUNDAMENTAL-001 — V1.5 CLOSEOUT

Date: 2026-10-04
Run: 37202007493
Artifact SHA256: `18bce2d5f73cb3ff05d02fc86407b8f92cd0d5064bb10c0f0a39c4886bc1f537`
Rule SHA256: `f3dd4dc2f809723557867ef858913a7d6608122e013c60af946989a1cd5b35c5`

## Source authority

Official EIA public XLS:
`WCESTUS1w.xls`

Series:
`WCESTUS1 — Weekly U.S. Ending Stocks excluding SPR of Crude Oil`

EIA source receipt:
- bytes: 130,048
- SHA256: `9076ac8edc312fa0497a2312f993b196b7408d4518568c8cac80a5a06179019a`
- parsed weekly records: 2,296
- mapped releases: 30 / 30
- all mapped current/prior observations are Friday week-ends
- all values positive
- verdict: `EIA_WCESTUS1_SOURCE_PASS`

MEXC discovery coverage:
- usable WTI event windows: 30 / 30

## Frozen hypothesis

Only:
- inventory DRAW => LONG WTI
- inventory BUILD => SHORT WTI

Magnitude thresholds:
- 0 kb
- 2,000 kb
- 5,000 kb

Entry:
MEXC Min5 open at T0+5m

Horizons:
5 / 15 / 30 / 60m

Inverse mode was not authorized.

## Scientific result

- pre-Holm eligible cells: 0
- Holm-selected cells: 0
- retrospective OOS: NOT AUTHORIZED / NOT OPENED
- forward candidate: NONE

Frozen verdict:
`NO_WTI_EIA_FUNDAMENTAL_DISCOVERY_CANDIDATE_AT_FROZEN_V15_GATE`

## Strongest descriptive cells — NOT candidates

### |inventory change| >= 5,000 kb / 15m

- N=14
- wins=8
- win rate=57.1429%
- mean gross=+11.1972 bps
- p=0.395264
- chronological third means:
  - -4.0849 bps
  - +23.5418 bps
  - +11.0782 bps

Fails stability and statistical gate.

### |inventory change| >= 5,000 kb / 30m

- N=14
- wins=9
- win rate=64.2857%
- mean gross=+3.9392 bps
- p=0.211975
- chronological third means:
  - +12.9867 bps
  - +4.4433 bps
  - -3.8029 bps

Fails stability and statistical gate.

### All non-zero changes / 5m

- N=30
- mean gross=+1.3670 bps
- win rate=40%
- p=0.899756
- first chronological third negative.

## Interpretation

The intuitive fundamental direction is not robust enough in the frozen Discovery.

Do NOT:
- invert BUILD/DRAW after seeing this result;
- change thresholds around 5M barrels;
- select a favorable horizon;
- rebrand September as pristine OOS.

V1.5 is CLOSED.

No live trading, accounts, credentials, wallets, private endpoints, orders, mutation, or main merge.
