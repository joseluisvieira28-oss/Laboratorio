# MSEL-001 — CHAIN INTERFACE FREEZE V0.1

Status: RESEARCH-ONLY / SOURCE-AUTHORITY FREEZE
Branch: `memecoin-structural-edge-v0.1`
Date: 2026-09-15

## 1. Purpose

Freeze the authoritative on-chain interfaces and regime-sensitive fields needed to reconstruct Pump.fun launch structure without using post-decision information.

This document does NOT authorize outcome opening, ML training, live trading, exchange mutation, deployment, or merge to main.

## 2. Authoritative program identities

### Pump bonding-curve program
Program ID: `6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P`

Source authority: official `pump-fun/pump-public-docs` repository / `PUMP_PROGRAM_README.md` and IDL.

Core lifecycle state:
- bonding curve PDA seeds: `["bonding-curve", mint]`
- `complete == false` while curve is active
- curve completion is set when `real_token_reserves == 0`
- permissionless `migrate(user, mint)` moves completed curves to PumpSwap when migration is enabled

Core curve state fields to reconstruct point-in-time:
- `virtual_token_reserves`
- `virtual_sol_reserves`
- `real_token_reserves`
- `real_sol_reserves`
- `token_total_supply`
- `complete`
- trailing upgrade fields when present, including creator / mode / quote fields

### PumpSwap program
Program ID: `pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA`

Source authority: official `pump-fun/pump-public-docs` repository / `PUMP_SWAP_README.md` and Pump AMM IDL.

Canonical migrated pools use index `0`. A canonical pool is treated as a lifecycle transition, not as a feature available before the migration transaction timestamp.

## 3. Creator identity caveat — HARD RULE

The Pump program documentation states that `user` and `creator` on coin creation can differ. In free-creation flows the first buyer can be the transaction signer while `creator` points to the original coin creator.

Therefore:
- transaction fee-payer / signer MUST NOT automatically be labelled creator;
- creator identity must be decoded from the instruction/event/account semantics valid at that historical timestamp;
- creator-history features are BLOCKED for any launch where creator identity cannot be reconstructed unambiguously.

## 4. Migration identity — HARD RULE

Do not infer graduation from current venue presence alone.

A launch is marked migrated only from a timestamped authoritative on-chain lifecycle event / instruction consistent with the historical Pump program version.

Migration timestamp must be strictly later than any pre-migration feature timestamp. A T+5m observation may include `curve_complete` only if completion occurred by T+5m; it may NOT include future migration status.

## 5. Protocol-regime changes — MUST NOT BE SILENTLY MIXED

Pump/PumpSwap have changed over time. Official public docs show additions including:
- creator-fee support;
- multiple fee-recipient changes;
- dynamic fee structures;
- Token-2022 / `create_v2` fields;
- SOL and USDC paired coins;
- holder-reward mode;
- cashback mode and later deprecation;
- additional BondingCurve / Pool trailing fields.

Consequences for MSEL-001:
1. historical account layouts must be decoded by transaction/account version, not by assuming today’s account length;
2. absent trailing fields on older accounts are not evidence of false/zero economics unless the historical schema says so;
3. SOL-paired and USDC-paired launches are separate populations until an explicit normalization is approved;
4. creator-fee / holder-reward / cashback regimes are separate strata;
5. fee assumptions must be historical point-in-time, not copied from the current fee page.

## 6. Transaction classes required for the pilot

For each mint, reconstruct in chronological order:
- creation transaction and create/create_v2 semantics;
- buy / buy_v2 / exact-quote-in variants as applicable;
- sell / sell_v2 variants as applicable;
- curve account state changes or event values sufficient to independently reconcile reserve deltas;
- migration event/instruction if it occurs;
- post-migration PumpSwap swaps only after migration timestamp.

No transaction is classified from transfer direction alone if the program instruction/event can be decoded directly.

## 7. Point-in-time wallet state

At T+1m, T+3m, T+5m:
- holder balances are reconstructed from transactions no later than the snapshot timestamp;
- protocol-owned / bonding-curve / pool accounts are excluded from economic holder concentration where appropriate;
- wallet funding relationships may use only funding events timestamped <= snapshot;
- prior-launch wallet reputation may use only launches whose relevant outcome window ended before the current launch timestamp.

## 8. Current-source vs historical-source distinction

The current official docs/IDL are authoritative for present program semantics and field definitions, but are NOT by themselves proof that every field/instruction existed historically.

Before the production backfill, each targeted historical period must receive a `SCHEMA_REGIME_MAP` tying:
- block/UTC interval
- observed instruction discriminators
- account lengths
- relevant program-upgrade boundary
- applicable fee regime

Unknown regime = FAIL CLOSED.

## 9. Source-gate decision

PASS for interface discovery:
- official Pump and PumpSwap program identities are known;
- lifecycle state and migration semantics are documented by the protocol;
- on-chain reconstruction is technically feasible in principle.

NOT YET PASS for production dataset:
- historical schema boundaries and fee boundaries still require machine-verifiable mapping;
- provider backfill completeness still requires a pilot reconciliation.

Next authorized artifact: `PILOT_RECONSTRUCTION_PROTOCOL_V01.md`.
