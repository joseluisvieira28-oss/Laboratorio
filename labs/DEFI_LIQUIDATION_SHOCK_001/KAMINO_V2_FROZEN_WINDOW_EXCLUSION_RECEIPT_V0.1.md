# DEFI-LIQUIDATION-SHOCK-001 — KAMINO V2 FROZEN-WINDOW EXCLUSION RECEIPT V0.1

Date: 2026-09-23  
Status: SOURCE AUTHORITY / OUTCOME-BLIND

Purpose: verify whether Kamino's later `liquidate_obligation_and_redeem_reserve_collateral_v2` instruction can contaminate the frozen 2023-2024 census of the already-authoritative V1 discriminator `b1479abce2854a37`.

Official repository checked: `Kamino-Finance/klend`.

Evidence:
- commit `c02bcf7dfe932af27d429df4111b3a3ca05a0dd3`, dated 2024-08-19, file `programs/klend/src/lib.rs`:
  - V1 liquidation instruction present;
  - V2 liquidation instruction absent.
- commit `796682e0e9f51ed8424632f9ad0f8c91540dbe68`, dated 2025-02-21, release message explicitly states "Introduce V2 instructions to avoid transaction introspection";
  - V1 present;
  - V2 present.

Frozen scientific census window ends `2025-01-01T00:00:00Z` exclusive.

Classification:

`KAMINO_V2_OUTSIDE_FROZEN_WINDOW_SOURCE_INTRODUCTION_2025-02-21`

Consequence:
- V2 discriminator `a2a1238f1ebbb967` MUST NOT be mixed into the 2023-2024 V1 census.
- The V1 census does not omit this later instruction variant within the frozen window.
- This receipt says nothing about trading edge or economic outcomes.

Firewall: prices=false; returns=false; pnl=false; direction=false; economic_outcomes=false; live_trading=false; orders=false; wallets=false; exchange_mutation=false; merge_main=false.
