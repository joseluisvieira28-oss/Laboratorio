# MSEL-001 — HISTORICAL SCHEMA LOCK V0.1

Status: FROZEN PRE-OUTCOME  
Pilot start: `2025-06-13T12:22:13Z`  
Branch: `memecoin-structural-edge-v0.1`

## Purpose

Prevent the June 2025 forensic pilot from being decoded with the current 2026 Pump protocol schema. Protocol evolution is itself a source of false features, mis-attribution and silent reconstruction error.

## Historical authority

For `pump-fun/pump-public-docs/idl/pump.json`, the latest public commit observed at or before the frozen pilot window is:

- commit: `e2b66e4fce2fc130955912315167dc41e56956ad`
- commit date: 2025-05-08
- message: `Add coin creator fee docs`

This commit is the schema authority for the initial decoder unless raw transactions prove an instruction/version not represented by that IDL. Such a mismatch is `SCHEMA_FAILURE`; it is not silently repaired with a newer IDL.

## Historical Pump program

Program ID:

`6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P`

Historical `create` discriminator:

`[24, 30, 200, 40, 5, 28, 7, 119]`

Hex:

`181ec828051c0777`

Historical `create` arguments, in Borsh order:

1. `name: string`
2. `symbol: string`
3. `uri: string`
4. `creator: pubkey`

The historical `create` account list includes `user` as a signer/payer-side account, while `creator` is an instruction argument. Therefore `creator != user` is valid and MUST be preserved.

## Identity model — mandatory

For every launch, retain distinct fields where reconstructible:

- `origin_creator`: creator pubkey embedded in the launch instruction.
- `tx_user`: Pump create instruction `user` account.
- `fee_payer`: Solana transaction fee payer.
- `seed_buyer`: launch-associated buyer in the same transaction, if present.
- `first_external_buyer`: first buyer outside protocol + origin/seed identity set.
- `curve_creator_at_snapshot`: creator stored in bonding-curve state as of the decision snapshot, if state history supports it.
- `fee_owner_at_snapshot`: fee-routing owner if distinct and point-in-time observable.

No field may be substituted for another merely because addresses often coincide.

## Creator mutations / CTO

Later Pump protocol versions expose creator-authority / takeover mechanics. Any creator mutation occurring after a decision snapshot is future information and cannot be back-propagated into T+1/T+3/T+5 features.

For the June 2025 pilot, the immutable `origin_creator` remains the attribution anchor for creator-history features unless a contemporaneous pre-snapshot mutation is independently proven.

## PumpSwap migration

PumpSwap program:

`pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA`

The historical Pump IDL already contains migration mechanics to PumpSwap. Migration after T+5 is an outcome/lifecycle event, not a T+5 feature. Migration before a snapshot may be represented only as contemporaneous lifecycle state.

## Fee-regime warning

Creator-fee mechanics were introduced before the June 2025 pilot, while the fee schedule changed substantially later. Therefore:

- never back-apply the 2026 Pump/PumpSwap fee schedule to June 2025 trades;
- reconstruction may initially ignore PnL fees while validating transaction/state integrity;
- before any economic backtest, historical fee parameters must be sourced as-of transaction time and frozen separately.

## Regime exclusions for the first pilot

The initial June 2025 pilot intentionally predates major later regime complications including Mayhem Mode and current `create_v2` Token-2022/custom-pair/holder-reward mechanics. They remain separate populations in later expansion.

## Failure conditions

Return `SCHEMA_FAILURE` and stop cohort promotion if any of the following occurs:

- a selected launch cannot be decoded deterministically under the historical authority;
- account-index resolution is ambiguous;
- creator/user extraction disagrees across independent decoders;
- raw transaction payload is incomplete for launch attribution;
- a newer schema is required but its activation boundary cannot be proven.

No outcomes may be opened to decide how to resolve a schema ambiguity.
