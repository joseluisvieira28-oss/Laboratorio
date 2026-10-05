# OPTIONS-VOL-FWD-001 V0.2 — SOURCE CALIBRATION CHUNK D CLOSEOUT

Date: 2026-10-05
Status: `SOURCE_CALIBRATION_INCOMPLETE`
Scientific outcomes opened: 0
MEXC data accessed: false

## Authoritative run

- Run: `37263283375`
- Job: `111614756565`
- Head: `717c708a840a194e749ae9cd2f3ed9c4b9d31e6d`
- Artifact: `v013-options-v02-sourcecal-d`
- Artifact id: `11330817725`
- Artifact digest: `sha256:3b6417f6cb0a46a97133282b0430e5fdd1af899c9ab509d16e915b69043b279c`

## Window

- first minute: `1791174240000`
- last minute: `1791184980000`
- observed minutes per symbol: 180

Chunk D first minute is strictly after Chunk C last minute `1791118800000`.
Non-overlap gate: PASS.

## Chunk D counts

BTC:
- observed: 180
- valid matched pairs: 179
- missing/invalid: 1
- source-only preview P95 |skew|: 2.3300000000000054 pp
- min skew: -2.4399999999999977 pp
- max skew: -1.3900000000000006 pp
- max absolute skew: 2.4399999999999977 pp

ETH:
- observed: 180
- valid matched pairs: 179
- missing/invalid: 1
- source-only preview P95 |skew|: 2.469999999999999 pp
- min skew: -2.6300000000000026 pp
- max skew: -0.14999999999999858 pp
- max absolute skew: 2.6300000000000026 pp

Source errors: 0.
Threshold committed: false.
Statistics run: false.
Event Futures outcomes opened: 0.
MEXC data accessed: false.

## Cumulative A+B+C+D state

Per symbol:
- unique observed minutes: 720
- BTC valid matched pairs: 682
- ETH valid matched pairs: 682
- duplicate time-window overlap: none by frozen chunk boundaries

Frozen activation prerequisite remains:
- >=1440 unique observed UTC minutes per symbol;
- >=1200 valid matched-pair minutes per symbol;
- zero unresolved integrity conflicts.

Therefore numeric thresholds may NOT yet be committed and no V0.2 Event Futures outcome may be opened.

The descriptive per-chunk P95 values above are not activation thresholds.

## Governance

The V0.1 5pp rule remains immutable.
V0.2 calibration uses Deribit public source only.
No payout/index/return/outcome data are used in calibration.
No login, private endpoint, account read, order, wallet, trading or main change.
