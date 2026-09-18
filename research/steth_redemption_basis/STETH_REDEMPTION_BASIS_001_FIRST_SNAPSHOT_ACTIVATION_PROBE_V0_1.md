# STETH-REDEMPTION-BASIS-001 — FROZEN FIRST-SNAPSHOT ACTIVATION PROVENANCE PROBE V0.1

Date: 2026-09-18
Status: FROZEN BEFORE PROBE / SOURCE-ONLY / OUTCOME-BLIND

## Purpose

Adjudicate whether the exact frozen first Discovery snapshot is source-valid under the original V0.1 authority.

No source-window, snapshot clock, contract, method, economic rule or outcome rule is changed.

## Immutable original rules

- source start: 2023-05-15T00:00:00Z
- later Discovery clock: one snapshot daily at 12:00 UTC
- expected snapshots: 597
- WithdrawalQueue proxy: 0x889edC2eDab5f40e902b864aD4d7AdE8E412F9B1
- queue historical state methods include getLastRequestId()
- source gate requires historical state accessibility near the beginning of the frozen period and feasibility for the exact fixed snapshots

## Provenance question

Was the frozen first daily snapshot at 2023-05-15T12:00:00Z capable of reading the canonical WithdrawalQueue V2 state, before the Lido V2 enactment later that day?

Public protocol provenance identifies the active WithdrawalQueue V2 implementation upgrade/enactment transaction as:
0x592d68a259af899fb435da0ac08c2fd500cb423f37f1d8ce8e3120cb84186b21

Reported activation block:
17266004

The probe must independently verify the transaction receipt/block through Ethereum RPC when available.

## Exact probe

Using the already-proven archive-capable provider set:
- https://eth-mainnet.public.blastapi.io
- https://rpc.mevblocker.io
- https://ethereum.blinklabs.xyz/

and quorum 2 where applicable:

1. deterministically map 2023-05-15T12:00:00Z to the first block at/after that timestamp;
2. retrieve WithdrawalQueue proxy bytecode at that frozen first-snapshot block;
3. call getLastRequestId() at that exact block;
4. retrieve the V2 activation transaction receipt and activation block;
5. call getLastRequestId() at the activation block;
6. record only accessibility/provenance facts, not economic queue values.

## Adjudication

If the proxy exists but getLastRequestId() is unavailable/reverts at the exact frozen 12:00 snapshot, while the same method is available at/after the verified V2 activation block:

classification = FROZEN_SOURCE_BOUNDARY_PROVENANCE_FAILURE

This is terminal for the exact frozen V0.1 source definition. It must NOT be relabelled SOURCE_AUTH_BLOCKED or NO_EDGE.

If the method is accessible at the frozen 12:00 snapshot with quorum:
classification = FROZEN_FIRST_SNAPSHOT_SOURCE_VALID

If evidence is unavailable/inconsistent:
classification = TECHNICAL_INCONCLUSIVE

## No rescue

This probe does NOT authorize:
- moving the source start;
- dropping the first snapshot;
- changing 12:00 UTC;
- starting after enactment;
- changing the expected 597 snapshot population.

Any such change would be a new prospectively defined experiment, not remediation of this exact frozen lab.

## Firewall

No Curve quote values.
No redemption predictor.
No ETH/stETH basis.
No market prices/returns.
No PnL/PF/drawdown.
No 2025/2026.
No live trading/orders/wallets/exchange mutation.
No main merge.
