# MEXC TESLA REGULAR-SESSION V0.2 — CLOSEOUT

Date: 2026-10-04
Run: 37229370865
Branch: `mexc-tesla-regsession-v0.2-prereg-2026-10-04`

## Source authority

Source gate:
- run `37229205842`
- verdict `TESLA_REGSESSION_PUBLIC_CORE_SOURCE_PASS`
- artifact SHA256 `9c55e9fc795c03fcdb71e66888b4351b0fb3da5dc8bb4ce1583dfc171f46dbbc`

Discovery artifact SHA256:
`66f923860b5a7782fb5407eb65cbf28c905b792b5fd7a3ea8c3c05f81fb5cd5d`

17 frozen sessions.
Exact common 1-minute observations: 4,573.

## Confirmatory cross-asset transfer

Family:
`MEXC-TESLA-NVDA-RULE-TRANSFER-001`

Exact transferred rule from NVIDIA V0.5:
- shock >= 5 bps
- lag gap >= 3 bps
- horizon 1 minute
- FOLLOW_EXTERNAL_CONSENSUS

Result:
- N=222
- signals on all 17 sessions
- wins=148
- win rate=66.6667%
- mean gross=+3.330474 bps
- median gross=+3.010349 bps
- chronological thirds=+3.478851 / +2.370311 / +4.142260 bps
- exact one-sided binomial p=3.836663e-7
- confirmatory alpha=0.025
- PASS=true
- illustrative net after 12 bps=-8.669526 bps

Classification:
`CROSS_ASSET_REPLICATION_SURVIVOR__FORWARD_VALIDATION_REQUIRED`

This is an independent asset replication of the exact NVIDIA rule. No parameter was selected from TESLA outcomes for this confirmatory result.

## Exploratory TESLA grid

Alpha budget:
`0.025`

Pre-Holm eligible cells:
12

Holm-selected cells:
3

Selected cells:

1. shock=5 / gap=3 / horizon=1m
   - N=222
   - wins=148
   - win rate=66.6667%
   - mean gross=+3.330474 bps
   - median=+3.010349 bps
   - p=3.836663e-7
   - Holm cutoff=0.000390625

2. shock=5 / gap=5 / horizon=1m
   - N=101
   - wins=71
   - win rate=70.2970%
   - mean gross=+4.891512 bps
   - median=+4.731612 bps
   - p=2.766535e-5
   - Holm cutoff=0.0003968254

3. shock=10 / gap=3 / horizon=1m
   - N=92
   - wins=65
   - win rate=70.6522%
   - mean gross=+4.093650 bps
   - median=+4.068517 bps
   - p=4.632022e-5
   - Holm cutoff=0.0004032258

All selected gross means remain below the standard MEXC API round-trip fee floor previously established for non-exempt Futures API execution.

## Frozen overall verdict

`TESLA_CROSS_ASSET_REPLICATION_SURVIVOR`

Scientific evidence strengthened from:
single-asset discovery -> independent cross-asset replication.

Execution feasibility remains separate.

No retrospective OOS, private endpoints, account reads, wallets, orders, exchange mutation or live trading were used.
