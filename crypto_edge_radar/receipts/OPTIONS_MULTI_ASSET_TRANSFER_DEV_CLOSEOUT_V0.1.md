# OPTIONS MULTI-ASSET TRANSFER — 2024 DEVELOPMENT CLOSEOUT V0.1

Date: 2026-10-02
Branch: `options-multiasset-fourhook-prep-v0.1-2026-10-02`
Workflow run: `36977686852`
Workflow head: `a71518c08a7a7f51a1aed242f9cc3feb7fd9bb8d`
Science freeze: `OPTIONS_MULTI_ASSET_TRANSFER_PRE_OUTCOME_FREEZE_V0.1`

## Final verdict

The exact BTC V2.1 mechanism was transferred unchanged to ETH, SOL and XRP and tested under the frozen 2024 Development gates.

- ETH: `DEV_REJECTED_EXACT_TRANSFER__2025_REMAINS_LOCKED`
- SOL: `DEV_REJECTED_EXACT_TRANSFER__2025_REMAINS_LOCKED`
- XRP: `DEV_REJECTED_EXACT_TRANSFER__2025_REMAINS_LOCKED`

No asset unlocked the one-shot 2025 OOS. Calendar 2025 therefore remains unopened for all three exact transfer candidates.

## ETH

Artifact: `11214292194`  
Artifact SHA256: `2a38577774c399d677cc08055d1bd209c32764fee1c46a5f5f3e0091ffab6a31`

Source:
- target option rows: 3,090,343
- eligible option rows after frozen DTE/moneyness/source filters: 161,763
- valid signal days: 363
- evaluable 2024 signal rows: 361
- duplicate trade IDs: 0
- parse failures: 0
- invalid IV rows rejected fail-closed: 6,682
- invalid index rows: 0
- 2024-12-30 and 2024-12-31 remained unresolved because resolving them would require 2025 outcome prices.

BASE10:
- entered scaled trades: 361
- average executed notional: 0.8029467820
- net mean: +8.4641213404 bps/opportunity
- profit factor: 1.0919204381
- cumulative net return: +35.7377840762%
- max drawdown: -48.4152540848%
- long / short: 186 / 175

Quarter net mean:
- Q1: +60.6147927459 bps, N=89
- Q2: -7.1321751925 bps, N=90
- Q3: +0.6395143138 bps, N=92
- Q4: -19.5123144451 bps, N=90

Hard gates A-G and I passed. Gate H failed:
- single-quarter share of total positive gross PnL = 88.0276210249%
- frozen maximum = 60%

Classification: REJECTED because the positive economics were excessively concentrated in one quarter. No 2025 rescue is permitted.

STRESS20 remained slightly positive:
- net mean: +0.4346535204 bps/opportunity
- profit factor: 1.0045099214
- cumulative net return: +1.5814742108%
- max drawdown: -55.2362421123%

STRESS20 is diagnostic only under the freeze and cannot rescue Gate H.

## SOL

Artifact: `11214795599`  
Artifact SHA256: `51389ef92b7eeea3ac2308d36b041d3269add71cbe5efb020f08ad0f306b4b3e`

Source:
- target option rows: 221,452
- eligible option rows: 9,930
- valid/evaluable signal days: 39
- duplicate trade IDs: 0
- parse failures: 0
- invalid IV rows rejected fail-closed: 657
- invalid index rows: 0

BASE10:
- entered scaled trades: 39
- average executed notional: 0.9657308389
- net mean: -2.7921240307 bps/opportunity
- profit factor: 0.9810424317
- cumulative net return: -1.0830210087%
- max drawdown: -14.5519027105%
- long / short: 37 / 2

Failed frozen gates:
- B: N >= 100
- D: positive BASE10 net mean
- E: PF > 1
- F: positive cumulative net return
- G: temporal breadth
- H: concentration <= 60%

Classification: REJECTED. 2025 remains locked.

## XRP

Artifact: `11213764604`  
Artifact SHA256: `3979b77efb4f8bec8147a41aff1bd0863473d11a52a32a75dc95d650a8a8e5bf`

Source:
- target option rows: 78,805
- eligible option rows: 2,401
- valid/evaluable signal days: 10
- duplicate trade IDs: 0
- parse failures: 0
- invalid IV rows rejected fail-closed: 313
- invalid index rows: 0

BASE10:
- entered scaled trades: 10
- average executed notional: 0.4597167163
- net mean: +177.1916193537 bps/opportunity
- profit factor: 2.1889697250
- cumulative net return: +19.3859837861%
- max drawdown: -7.3054776468%
- long / short: 9 / 1

The apparent economics are not promotion evidence because the sample is only N=10 and is concentrated almost entirely in Q4.

Failed frozen gates:
- B: N >= 100
- G: temporal breadth
- H: concentration <= 60%

Classification: REJECTED. 2025 remains locked.

## Governance / protected data

For ETH, SOL and XRP:
- holdout 2025 accessed: false
- 2026 accessed: false
- live trading authorized: false
- exchange mutation: false
- main merge: false
- no post-outcome rescue performed

The prepared 2025 OOS workflow remains dormant. No OOS trigger is authorized or created because no Development candidate passed all frozen gates.

## Operational consequence

The proposed one-rod / four-hook architecture is source-feasible, but the exact BTC V2.1 scientific identity did not qualify for promotion on ETH, SOL or XRP.

BTC remains a separate existing OPTIONS V2.1 lineage. ETH/SOL/XRP must not be added as live hooks under this exact transfer identity.
