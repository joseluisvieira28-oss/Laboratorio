# AAVE-LIQUIDATION-OVERHANG-001 — ARCHIVE RPC REPLACEMENT SOURCE FEASIBILITY V0.2B

Date: 2026-09-18
Branch: `aave-liquidation-overhang-v0.1`
Status: **FROZEN BEFORE NETWORK PROBE / SOURCE-ONLY / OUTCOME-BLIND**

## Upstream evidence

Canonical R1 sharded audit V0.2A run `35375172202` completed all deterministic borrower-census and scaled-token replay stages but classified:

`RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE`

The receipt contains 77 validation targets and 77 failures, all:
`INSUFFICIENT_ARCHIVE_RPC_QUORUM`.

The original five endpoint set produced zero usable target values. No health factor, liquidation-overhang predictor, future outcome, price return or PnL was opened.

## Purpose

Test a prospectively frozen replacement provider set for historical Ethereum state access before any target balance is queried through those providers.

This probe tests only historical `eth_call` capability and JSON-RPC batch compatibility on a constant ERC-20 metadata method.

## Frozen historical blocks

Exactly:
- 17,748,972
- 19,007,945
- 20,266,917
- 21,525,890

## Frozen harmless call

Contract:
`0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48` (USDC)

Method:
`decimals()`

Calldata:
`0x313ce567`

The returned value is source-capability metadata only and MUST NOT be printed or persisted numerically. The probe may persist only:
- HTTP status;
- response shape;
- per-request success/error;
- result byte length;
- SHA-256 of the opaque result bytes;
- whether all four calls return identical opaque hashes;
- latency/transport counters.

## Frozen candidate endpoints

1. `https://ethereum.rpc.subquery.network/public`
2. `https://eth.merkle.io`
3. `https://eth-mainnet.public.blastapi.io`
4. `https://ethereum.blockpi.network/v1/rpc/public`
5. `https://eth.api.onfinality.io/public`
6. `https://endpoints.omniatech.io/v1/eth/mainnet/public`
7. `https://rpc.flashbots.net`

No endpoint may be added after observing this probe.

## Per-endpoint PASS

An endpoint passes only if:
- a single historical `eth_call` succeeds at every frozen block;
- one batch request containing the four calls returns a JSON list;
- all four batch items are present with non-error hex results;
- opaque result hashes agree between single-call and batch mode for each block;
- no authentication is required.

## Overall source-feasibility PASS

`ARCHIVE_RPC_REPLACEMENT_SOURCE_PASS` requires at least **3** independent candidate endpoints to pass all criteria.

Anything below 3 is `ARCHIVE_RPC_REPLACEMENT_SOURCE_INSUFFICIENT`.

This probe does not change the original R1 requirement: later target validation must still have at least **2** usable independent endpoint values and exact equality per target.

## Post-pass authority

A feasibility PASS permits a separate immutable provider-set amendment naming only endpoints that passed this probe, followed by rerunning only the frozen V0.2A target validation against the exact already-produced target set.

It does not authorize changing:
- borrower sample;
- replay ledger;
- reserves;
- audit blocks;
- arithmetic;
- target values;
- quorum;
- equality/reconciliation rules.

## Safety

Forbidden:
- reading `scaledBalanceOf` for any R1 target in this feasibility probe;
- health factor;
- liquidation overhang;
- prices/returns/PnL;
- 2025/2026 market data;
- trading, wallets, exchange mutation, orders, alerts/webhooks;
- merge to main.
