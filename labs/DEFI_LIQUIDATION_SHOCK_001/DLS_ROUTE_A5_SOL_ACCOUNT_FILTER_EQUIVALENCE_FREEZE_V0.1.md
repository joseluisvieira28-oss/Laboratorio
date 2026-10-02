# DLS ROUTE A5 — SOL SOURCE-ACCOUNT FILTER EQUIVALENCE FREEZE V0.1

Date: 2026-10-02
Status: FROZEN SOURCE/TRANSPORT ONLY — PROTECTED 2025 MARKET OUTCOMES CLOSED
Branch: dls-field-enrichment-v01

## Purpose
Test a target-specific historical transport route for the already-frozen DLS strategy population:
LIQUIDATED_COLLATERAL_SOL.

The route queries exact source-authoritative SOL collateral reserve/bank/vault accounts instead of
the full high-traffic protocol program address. It may advance only if it exactly reproduces the
canonical 2024 SOL cluster census.

This changes no scientific event definition, protocol/class, mint, quiet-window, source role,
direction, strategy, timing, cost or economic gate.

## Canonical truth
Immutable Source Cluster Sample Gate:
- run 36465385517
- artifact 10988887983
- artifact SHA256 7703f53869df186d20cf5c339327a1df2ee3f433c7ff0f8e6a02e1b9d053d97
- target identity mint:So11111111111111111111111111111111111111112
- canonical OOS/2024 SOL clusters: exactly 9,931
- canonical Discovery SOL clusters: 5,672
- target total: 15,603

A5 equivalence is adjudicated on 2024 only. Protected 2025 stays closed.

## Frozen account set — 13 addresses

### Marginfi asset_bank accounts resolving to SOL
Source authority: MARGINFI_BANK_UNIT_REGISTRY_POPULATION_PASS
run 36312418451 / artifact 10929339072.

- BpmLoZcyKJP9Jncq5TE7TTzxPV6PSbKNZkuvU1MB6t8e
- CCKtUs6Cgwo4aaQUmBPmyoApH2gUDErxNZCAntD6LYGh

Role condition after decode:
canonical lending_account_liquidate accounts[1] must equal one of the two addresses.

### Save0c withdraw_reserve accounts resolving to SOL
Source authority: SAVE0C_UNIT_METADATA_POPULATION_PASS V0.3
run 36464764538 / artifact 10989451796.
The V0.3 terminal registry has 30/30 target reserves resolved, zero pending/conflicts; four map to SOL.

- 3WPYWiZtc2uJq1JiF3Z3KswicFAp5VrFgEHwP3CkuDUn
- 7trBAMkVU8dcPQVdScz7VNywZwqnD1rwXkwkVPQJ95bT
- 8xogd14bBxBdGKDfkDciPPp6pZ3Cw4Yj5USRbGJDbZpA
- UTABCRXirrbpCNDogCoqEECtM3V44jXGCsK23ZepV3Z

Role condition:
canonical LiquidateObligation accounts[4] must equal one of the four reserve addresses.

### Kamino withdraw_reserve_liquidity_supply account resolving to SOL
Source authority: Kamino unit metadata V0.3, run 36278635010.
Across every canonical Kamino unit partition 2024-03 through 2024-12:
24,361 / 24,361 collateral-underlying SOL events use the same fixed first source account:

- GafNuUXj9rxGLn4y79dPu6MHSuPWeJR6UtTWuexpGh3U

Role condition:
canonical liquidate_obligation_and_redeem_reserve_collateral SOL-liquidity-supply role must equal GafNu...
Dynamic user destination accounts are explicitly NOT part of the filter set.

### Save11 primary withdraw_reserve_liquidity_supply accounts resolving to SOL
Source authority: Save11 V0.4 unit metadata, run 36313729668.
Across 2024-07 through 2024-12, 4,550 SOL-collateral events resolve to exactly these six
primary source accounts:

- 8UviNr47S8eL6J3WfDxMRa3hvLta1VDJwNWqsDgtN3Cv
- 5cSfC32xBUYqGfkURLGfANuK64naHmMp27jUT7LQSujY
- 8jVVXXxzC9N5FeHUxKBgXLM8xARzLpnzXz8dqZHzpykY
- APJAFijv9XrtnrAvktzsqgJboq4Uhs3mu7YN7DQ5bFMH
- 6ToFgS59GXhYMoHHL2GNPh5aNypxc1UAR1RYpfdHftBE
- 6s8hmMLgdhpffsL7H9neZBhFSxaQYTnQ1gkjaRN25GS7

Role condition:
canonical LiquidateObligationAndRedeemReserveCollateral account[8] must equal one of these six.
Optional user destination account[2] is not a filter authority.

## Stage A — capacity
Query signatures-only gTFA for each of the 13 frozen addresses over:
2024-01-01T00:00:00Z <= blockTime < 2025-01-01T00:00:00Z.

- status=succeeded
- sortOrder=asc
- limit=1000
- deterministic pagination
- hard ceiling 25 pages/address

PASS requires every address terminate <=25 pages.
Failure is A5_CAPACITY_BLOCKED, not NO_EDGE.

## Stage B — exact 2024 equivalence
Only if Stage A passes:
- query full transaction history for the same 13 addresses and exact 2024 window;
- deduplicate by transaction signature before canonical instruction decoding;
- use A2-validated RAW normalizer/decoder semantics;
- retain only the four frozen liquidation classes and exact role-account conditions above;
- each matching instruction is one realized source event;
- timestamp = explicit transaction blockTime;
- cluster separately by protocol/class/mint using exact frozen 60-second quiet rule;
- compute cluster_id exactly as build_source_cluster_sample_gate_v0_1.py.

ROUTE_A5_SOL_ACCOUNT_EQUIVALENCE_PASS requires ALL:
- exactly 9,931 reconstructed 2024 SOL clusters;
- exact cluster_id set equality with canonical census;
- missing cluster IDs = 0;
- extra cluster IDs = 0;
- for every cluster: protocol, instruction_class, first/last timestamps, event_count,
  first/last signature and T0 exact;
- source decode anomalies = 0;
- duplicate canonical instructions = 0.

Any mismatch => ROUTE_A5_SOL_ACCOUNT_EQUIVALENCE_BLOCKED.

## 2025 firewall
A5 2024 PASS does NOT itself prove no new SOL reserve/bank was created during 2025.
A separate pre-2025-source registry extension gate is mandatory before A5 may collect protected 2025:
- discover SOL account-set changes using protocol-native/source-only metadata;
- never use 2025 prices/returns/PnL to select accounts;
- preserve every newly source-proven SOL account.

No Protected-2025 economic holdout may open until a real PROTECTED_2025_SOURCE_AUTHORITY_PASS exists.

No purchase/upgrade.
No 2026 data.
No main merge.
No trading/orders/wallet/exchange mutation.
Trading authority: NONE.
