# DEFI-LIQUIDATION-SHOCK-001 — DRIFT FIELD ENRICHMENT POPULATION FREEZE V0.1

Date: 2026-09-26
Status: FROZEN SOURCE-ONLY / OUTCOME-BLIND / LAUNCH BLOCKED UNTIL FINAL DRIFT SOURCE PASS

## Launch prerequisite

This enrichment MUST NOT launch until the actual terminal artifact from the final Drift source reassembly
classifies:

`DRIFT_FOUR_CLASS_EVENT_CENSUS_SOURCE_PASS`

and RAW reconciliation passes with sample_count == pass_count > 0.

## Population

Frozen Drift source interval:
`[2022-11-04T15:17:54Z, 2025-01-01T00:00:00Z)`

Frozen classes:
- liquidate_perp
- liquidate_spot
- liquidate_borrow_for_perp_pnl
- liquidate_perp_pnl_for_deposit

No class may be added/dropped because of enrichment or future outcomes.

## Baseline evidence topology

Use only evidence admitted by SOURCE_EVIDENCE_REASSEMBLY_SELECTION_FREEZE_V0.1.

Original complete monthly evidence is used for:
- 2022-11
- 2022-12
- 2023-01
- 2023-02
- 2023-03
- 2023-04
- 2023-07
- 2023-08
- 2023-10
- 2023-11
- 2024-01

Replacement shards are used for:
- V0.1: 2023-05, 2023-06
- V0.2: 2023-09, 2023-12
- V0.3: 2024-02 through 2024-05
- V0.4: 2024-06 through 2024-12

Cancelled/partial original artifacts for replacement months remain excluded.

## Enrichment query

Re-query SQD finalized-stream over each exact accepted evidence interval using:
- frozen Drift program ID;
- programId-only enumeration;
- local decoding of the four frozen discriminators;
- exact UTC local filtering;
- identical success-state semantics;
- instruction accounts;
- full instruction data.

Do not request token balances, decimals, prices or economic outcomes.

## Canonical exact join

Key:
`drift + class + signature + instructionAddress`

Each enrichment partition requires:
- missing=0
- extra=0
- duplicate=0
- identity conflict=0
- source anomaly=0

No event may be dropped because semantic fields are missing.

## Common account roles

All four classes require at least six fixed accounts:
0 state
1 authority
2 liquidator
3 liquidatorStats
4 user — liquidated user
5 userStats

Remaining accounts are retained as dynamic market/oracle context but are not assigned unsupported fixed semantics.

## Argument identity fields

Only non-economic market identifiers may be emitted from instruction arguments.

### liquidate_perp
- bytes after discriminator begin with `marketIndex:u16`
- emit `perp_market_index`
- do NOT emit liquidatorMaxBaseAssetAmount or limitPrice
- allowed encoded lengths under frozen ABI: 19 bytes (None limit) or 27 bytes (Some limit)

### liquidate_spot
- emit `asset_spot_market_index:u16`
- emit `liability_spot_market_index:u16`
- do NOT emit liquidatorMaxLiabilityTransfer or limitPrice
- allowed encoded lengths: 29 or 37 bytes

### liquidate_borrow_for_perp_pnl
- emit `perp_market_index:u16`
- emit `spot_market_index:u16`
- do NOT emit liquidatorMaxLiabilityTransfer or limitPrice
- allowed encoded lengths: 29 or 37 bytes

### liquidate_perp_pnl_for_deposit
- emit `perp_market_index:u16`
- emit `spot_market_index:u16`
- do NOT emit liquidatorMaxPnlTransfer or limitPrice
- allowed encoded lengths: 29 or 37 bytes

## Aggregate PASS

Every accepted source interval must have a PASS enrichment receipt.

Aggregate requirements:
- exact baseline/enriched population equality;
- every realized event has >=6 instruction accounts;
- every event matches its class-specific allowed ABI data length;
- market-index identity fields decode deterministically;
- zero missing/extra/duplicate/conflict/anomaly counts.

Terminal:
`DRIFT_FIELD_ENRICHMENT_POPULATION_PASS`

## Firewall

prices=false
usd_notional=false
returns=false
pnl=false
direction=false
economic_outcomes=false
token_balances=false
token_amounts=false
token_decimals=false
limit_price_values=false
requested_max_amount_values=false
protected_2025_2026_market_outcomes=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
paid_source=false
account_creation=false
post_outcome_tuning=false
merge_main=false
