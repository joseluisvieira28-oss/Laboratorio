# DEFI-LIQUIDATION-SHOCK-001 — DIRECTION SOURCE AUDIT FREEZE V0.1

Date: 2026-09-29
Status: FROZEN / SOURCE-ROLE ONLY / BEFORE 2025 HOLDOUT

## Prerequisite
- canonical OOS lock: SURVIVES_OOS
- canonical OOS run: 36486620726
- canonical OOS artifact: 10998958189
- 2025/2026 outcomes remain closed.

## Purpose
Determine whether the already-frozen SOL liquidation population contains a protocol-native economic role that can support a prospective directional hypothesis without using any 2025/2026 price outcome.

This audit does NOT claim that collateral receipt equals an executed market sale.

## Pinned source construction
Pinned builder blob:
`labs/DEFI_LIQUIDATION_SHOCK_001/source/build_source_cluster_sample_gate_v0_1.py`
Git blob SHA: `0179427f0cef0da0630f8edcc8240056708fd445`.

For lending protocols, the frozen primary market identity is constructed from:
- Marginfi: `asset_bank` resolved to mint; `liab_bank` is not used as primary market.
- Save0c: `collateral_underlying` from `withdraw_reserve`.
- Kamino: `collateral_underlying`.
- Save11: `collateral_underlying`.

Therefore a SOL primary-market cluster is, by construction, a liquidation where SOL is on the collateral/asset side of the source event.

## Audit population
Use exactly the immutable `SOURCE_PRIMARY_CLUSTER_CENSUS_V0.1.ndjson` from Source Cluster Sample Gate run 36465385517 / artifact 10988887983.

Target:
`mint:So11111111111111111111111111111111111111112`

Expected frozen counts:
- Discovery: 5,672
- OOS: 9,931
- total: 15,603

Allowed protocol/class rows:
- marginfi / lending_account_liquidate
- save0c / LiquidateObligation
- kamino / liquidate_obligation_and_redeem_reserve_collateral
- save11 / LiquidateObligationAndRedeemReserveCollateral

No Drift row is allowed in the SOL target population.

## Classifications
PASS:
`DIRECTION_SOURCE_ROLE_AUDIT_PASS`
only if every target cluster is attributable to the frozen collateral-side construction above, counts exactly match, and no unknown protocol/class exists.

BLOCKED:
`DIRECTION_SOURCE_ROLE_AUDIT_BLOCKED`
otherwise.

## Direction semantics
A PASS establishes only:
`SOURCE_ROLE = LIQUIDATED_COLLATERAL_SOL`

It does NOT establish:
- that the liquidator sold SOL;
- venue-specific aggressive sell flow;
- guaranteed negative next return;
- executable SHORT profitability.

The prospective economic hypothesis permitted after PASS is:
`H_SHORT_COLLATERAL_LIQUIDATION_V0.1`: after a qualifying SOL-collateral liquidation cascade, test a SHORT translation prospectively.

This hypothesis is allowed because it is fixed from source-role mechanics before 2025 outcomes are opened. It remains unproven until the protected economic holdout.

## Firewall
prices_2025_2026_opened=false
returns_2025_2026_opened=false
pnl_2025_2026_opened=false
directional_2025_2026_outcomes_opened=false
post_outcome_tuning=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
