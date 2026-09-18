# AAVE-LIQUIDATION-OVERHANG-001 — R1 SHARDED RECOVERY V0.2 TECHNICAL CLOSEOUT

Date: 2026-09-18
Branch: `aave-liquidation-overhang-v0.1`

## Canonical status

Run `35379166810` is CLOSED as:

`RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE / SUPERSEDED_PROVIDER_SET_PATH`

This is NOT a scientific failure and is NOT evidence against the liquidation-overhang mechanism.

## What succeeded

- deterministic sample derivation: PASS;
- exactly 16 frozen borrowers;
- eight fixed source/replay shards: 8/8 PASS;
- no variable-debt BalanceTransfer provenance violation was reported by the aggregate receipt;
- no negative replay state was reported;
- replay reconstructed exactly 77 validation targets;
- no health factor, overhang, market price, return or PnL was opened.

## Exact failure

The canonical aggregate artifact:

- run: `35379166810`
- artifact: `10561454684`
- artifact digest: `sha256:0244ab2c9a591d432b29f5483492192e1c9273f9193f66b1472682a4b6f34396`

classified:

`RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE`

with:

- validation targets: 77;
- validation failures: 77;
- each target failed through `INSUFFICIENT_ARCHIVE_RPC_QUORUM`;
- validated targets: 0.

The reason is operational lineage, not changed replay science: `aggregate_r1_scaled_ledger_audit_v02.py` explicitly calls the original frozen V0.1 `validate_targets`, which uses the older archive-RPC endpoint set. That endpoint set was already superseded prospectively for target validation by the separately frozen V0.2D provider-set amendment.

## Superseding valid authority

The exact 77-target population was separately revalidated under:

`AAVE_LIQUIDATION_OVERHANG_001_R1_TARGET_VALIDATION_PROVIDER_SET_AMENDMENT_V0_2D`

using the prospectively frozen provider set:

- `https://eth-mainnet.public.blastapi.io`
- `https://rpc.mevblocker.io`
- `https://ethereum.blinklabs.xyz/`

Quorum remained exactly 2 and equality remained exact.

V0.2D run `35378340649`: SUCCESS.

Canonical reconciliation V0.2E run `35378692311`: SUCCESS / exact receipt `R1_AUDIT_PASS`.

The currently running V0.3 continuation `35378904880` is pinned to V0.2E and therefore is the canonical continuation path.

## Decision

Do NOT rerun or patch run `35379166810`.

Do NOT treat its 77 quorum failures as new scientific evidence.

Do NOT change target population, quorum, equality, borrower sample, audit blocks, replay arithmetic or provider set after outcomes.

Preserve this run as a technical/superseded closeout to prevent duplicate recovery attempts.

## Safety

2025/2026 outcomes unopened.
Health factor not computed.
Overhang not computed.
Market returns unopened.
PnL unopened.
No live trading.
No orders.
No wallets.
No exchange mutation.
No main merge.
