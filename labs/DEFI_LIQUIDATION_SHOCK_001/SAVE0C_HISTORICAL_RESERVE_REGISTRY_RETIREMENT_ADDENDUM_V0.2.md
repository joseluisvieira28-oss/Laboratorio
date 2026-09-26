# DEFI-LIQUIDATION-SHOCK-001 — SAVE0C HISTORICAL RESERVE REGISTRY RETIREMENT ADDENDUM V0.2

Date: 2026-09-27
Status: FROZEN SOURCE-ONLY / OUTCOME-BLIND

## Trigger

Historical registry V0.1 found two commits touching:
`solendprotocol/solend-sdk/src/configs/production.json`

- c93fbc81fcc68610ad64fbce4a170a38335b7d7f — 2021-12-08T18:42:46Z — initial file
- a20ebb461c846c9043f8ba1cc26fc822056853d2 — 2022-01-10T01:15:03Z — file explicitly removed

GitHub commit metadata for a20ebb... records:
`src/configs/production.json status=removed, deletions=265`

Therefore the missing file at the second commit is a documented source retirement, not a parser/fetch contradiction.

## Correct taxonomy

The historical registry may prove only the exact reserve identities present in the last available authenticated snapshot before retirement.

It MUST NOT claim coverage after:
`2022-01-10T01:15:03Z`

Classification:
`SAVE0C_HISTORICAL_RESERVE_REGISTRY_PARTIAL_SOURCE_COVERAGE`

This classification is usable only as a bounded historical source subset. It is not equivalent to:
`SAVE0C_HISTORICAL_RESERVE_REGISTRY_SOURCE_PASS`

## Frozen V0.2 rules

For every commit touching the path:
- parse existing file snapshots;
- if the path is explicitly removed in that commit, record a retirement event rather than an error;
- any 404 without explicit removal remains fail-closed;
- preserve exact registry identities from authenticated snapshots;
- preserve coverage_end equal to the explicit retirement timestamp.

Historical entries may only be applied within a later completion procedure under a separately frozen temporal/applicability rule. They may not silently resolve post-retirement events.

## Consequence

If Save0c V0.1 unit aggregate is PARTIAL_SOURCE_COVERAGE:
- V0.2 current finalized-RPC dataslice fallback remains the primary general completion path;
- the V0.2 historical registry may be used only for event/reserve cases whose applicability is independently proven;
- no missing reserve may be guessed.

## Firewall

prices=false
oracle_values=false
usd_notional=false
returns=false
pnl=false
direction=false
economic_outcomes=false
reserve_amounts=false
token_amounts=false
protected_2025_2026_market_outcomes=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
paid_source=false
account_creation=false
post_outcome_tuning=false
merge_main=false
