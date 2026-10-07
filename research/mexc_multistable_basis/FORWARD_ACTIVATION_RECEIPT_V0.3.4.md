# MEXC-MULTI-STABLE-BASIS-001 — FORWARD ACTIVATION RECEIPT V0.3.4

Date: 2026-10-07
Status: PROSPECTIVE_ACTIVE / OUTCOME-SEALED UNTIL READINESS

## Canonical authority
- PROSPECTIVE_PREOUTCOME_FREEZE_V0.3.md
- freeze commit: bbc8291d0302f6776f75cb19d8c62df16b68bf25
- CALIBRATION_THRESHOLD_RECEIPT_V0.3.md
- threshold commit: 289fddb48ffbe34421914d2356eb5fa7f7f20ea7
- FORWARD_TIMESTAMP_CLARIFICATION_V0.3.2.md
- FORWARD_SOURCE_COMPLETENESS_AMENDMENT_V0.3.3.md
- PREACTIVATION_COMPLETENESS_CLARIFICATION_V0.3.4.md

## Frozen thresholds
- BTC q99 = 7.464945216995034 bps
- ETH q99 = 9.80929964899957 bps

Calibration authority:
- workflow run 37646147602
- 11,520 / 11,520 exact common minutes for BTC
- 11,520 / 11,520 exact common minutes for ETH
- economic outcomes opened during calibration: false

## Pre-activation superseded run
The following is permanently NON-ADMISSIBLE:
- trigger commit: 33f2c9aaf813820d78117bb762bfc782d41ade26
- workflow run: 37647073714
- segment: 2026-10-07_1600_1859

Reason:
it preceded the V0.3.4 clarification that requires executable evidence for funding-eligible raw triggers even when cooldown-suppressed.

No output from that run may enter scientific aggregation.

## Pre-activation hardening
Forward collector self-test:
- run 37647535601 = SUCCESS

Sealed adjudicator self-test:
- run 37648156617 = SUCCESS
- empty / underpowered epochs remain PROSPECTIVE_ACCUMULATING
- economic_metrics_opened = false before frozen readiness

## First authoritative forward activation
- trigger commit: 7d45c4cb4ba151de5ed079a438fe18b779df1aa0
- workflow run: 37647670800
- segment: 2026-10-07_1600_1859_authv034
- start: 2026-10-07T16:00:00Z
- end: 2026-10-07T18:59:00Z
- state at activation receipt: in_progress / Prospective forward capture

## Frozen readiness
No economics may be adjudicated until ALL:
- >=40 admitted event baskets
- >=7 distinct UTC dates
- BTC >=10 admitted underlying trades
- ETH >=10 admitted underlying trades
- max one-date concentration <=35%
- scheduled scan completeness >=99%
- execution completeness >=95%
- zero unresolved evidence conflicts

Before readiness:
`PROSPECTIVE_ACCUMULATING`

Terminal outcomes remain exactly:
- `SURVIVES_PROSPECTIVE_MULTI_STABLE_BASIS_V03`
- `NO_EDGE_PROSPECTIVE_AT_FROZEN_V03_GATE`
- `BLOCKED_DATA_QUALITY`
- `EXECUTION_SOURCE_BLOCKED`

## Governance
No main merge, live trading, orders, private/authenticated endpoints, account reads, wallets, exchange mutation, spending, backfill or post-outcome tuning.
