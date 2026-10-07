# MEXC-MULTI-STABLE-BASIS-001 — CALIBRATION THRESHOLD RECEIPT V0.3

Date: 2026-10-07
Status: IMMUTABLE THRESHOLD AUTHORITY / OUTCOME SEAL STILL CLOSED

Scientific freeze:
- `PROSPECTIVE_PREOUTCOME_FREEZE_V0.3.md`
- freeze commit: `bbc8291d0302f6776f75cb19d8c62df16b68bf25`

Technical remediation:
- `CALIBRATION_TRANSPORT_REMEDIATION_V0.3.1.md`
- no scientific rule changed

Authoritative calibration run:
- workflow run: `37646147602`
- runner head: `a40f0c7b77dc0b9fb389fd1d92085ae90f1bcd6b`
- artifact: `mexc-multistable-calibration-v03-37646147602`
- artifact id: `11493203906`
- artifact digest: `sha256:3a798216e47e44bab9072596ca80e1408b710c60ba9acc3f36b1f15d9c95777b`

Frozen calibration window:
`2026-09-29T00:00:00Z <= t < 2026-10-07T00:00:00Z`

Coverage:
- expected minutes per underlying: 11,520
- BTC exact common minutes: 11,520 (100%)
- ETH exact common minutes: 11,520 (100%)
- frozen minimum: 95%

Threshold method:
nearest-rank q99 of frozen normalized cross-stablecoin range_bps.

IMMUTABLE THRESHOLDS:
- BTC: `7.464945216995034 bps`
- ETH: `9.80929964899957 bps`

Machine verdict:
`CALIBRATION_THRESHOLD_PASS`

Invalid predecessor:
Run `37645886508` had only 8,000/11,520 common minutes because Spot paging returned 500 rows per request. Its provisional q99 values are invalid and have no authority.

Outcome-access declaration at threshold freeze:
- economic outcomes opened: false
- forward returns calculated: false
- execution PnL calculated: false
- alternative horizons tested: false

Prospective economic boundary:
Only fully closed minutes strictly AFTER the commit timestamp that first adds this threshold receipt may be admitted.
No backfill.

No-rescue:
These BTC/ETH q99 thresholds may not be changed after this receipt because later outcomes are attractive or unattractive.
