# DEFI-LIQUIDATION-SHOCK-001 — OOS EXECUTION IMPLEMENTATION BINDING V0.1

Date: 2026-09-28
Status: BINDING IMPLEMENTATION / NO SCIENTIFIC RULE CHANGE

## Prerequisite

Discovery is terminal:
SURVIVES_DISCOVERY

Canonical Discovery:
- run 36485119508
- artifact 10997938881
- DISCOVERY_RESULT_RECEIPT_V0.1.json SHA256:
  e8bd60398111339f95b82302fe22335665959949adfc357a6ee89d3c1c318a0c
- adjudication lock commit:
  3e9299bc849f2b6928af5d3e080bbc3755c76536

This binding opens OOS only because OOS_AFTER_DISCOVERY_ADJUDICATION was already authorized by FINAL_PRE_DISCOVERY_AUTHORITY_PASS.

## Frozen OOS split

Use only:
2024-01-01T00:00:00Z <= T0 < 2025-01-01T00:00:00Z

No 2025/2026 market payload may be opened.

Any event/control whose required 240-minute horizon would cross into 2025 is ineligible under the protected-holdout firewall. The OOS split is not widened.

## Exact inherited implementation

OOS inherits without change from:
- OUTCOME_STATISTICAL_AUTHORITY_FREEZE_V0.1.md
- PRE_DISCOVERY_TEMPORAL_HOLDOUT_FREEZE_V0.1.md
- DISCOVERY_EXECUTION_IMPLEMENTATION_FREEZE_V0.1.md

Unchanged:
- direct market mapping;
- Binance DAILY Spot 1m archive authority;
- checksum verification;
- REST reconciliation procedure;
- T0 -> first minute boundary alignment;
- horizons 1m / 5m / 30m / 240m;
- primary 5m outcome;
- same-month / same-UTC-hour deterministic control;
- +/-4h event exclusion;
- SHA256 control ranking serialization;
- calendar-day block bootstrap, 5,000 repetitions;
- 10% relative-uplift guardrail;
- no proxy rescue;
- no post-outcome tuning.

## OOS inferential families

For OOS family-level reporting, include source-only subgroups whose post-mapping status is either:
- INFERENTIAL_DISCOVERY_AND_OOS; or
- EXTERNAL_CONFIRMATORY_INFERENTIAL.

Subgroup pair coverage must remain >=90%.
Pooled OOS pair coverage must remain >=95%.

## OOS verdict

MARKET_DATA_SOURCE_BLOCKED:
source integrity or required pair coverage fails.

Otherwise OOS passes only if ALL frozen conditions hold:
1. paired OOS N >= 500;
2. mean(D_5m) > 0;
3. lower 95% day-block bootstrap CI for mean(D_5m) > 0;
4. 5m relative uplift >=10%;
5. at least two inferential protocol families have positive 5m mean paired difference;
6. at least two secondary horizons have positive paired mean difference.

All pass:
SURVIVES_OOS

Otherwise:
NO_EDGE_OOS

Secondary Holm results may be reported descriptively/supportively, but are not an added OOS gate because OUTCOME_STATISTICAL_AUTHORITY_FREEZE_V0.1.md does not require them for OOS PASS.

## Firewall before OOS payload access

oos_2024_opened=false
protected_2025_2026_opened=false
post_outcome_tuning=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
