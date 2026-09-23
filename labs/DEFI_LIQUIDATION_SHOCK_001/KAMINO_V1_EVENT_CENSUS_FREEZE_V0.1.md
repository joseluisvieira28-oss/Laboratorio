# DEFI-LIQUIDATION-SHOCK-001 — KAMINO V1 EVENT CENSUS FREEZE V0.1

Date: 2026-09-23
Status: FROZEN PRE-EXECUTION / SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED

## Scientific identity

Program:
`KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD`

Authoritative liquidation class:
`liquidate_obligation_and_redeem_reserve_collateral`

Frozen discriminator:
`b1479abce2854a37`

RAW-verified first-success boundary:
- UTC: `2023-11-17T14:48:24Z`
- slot: `230572965`
- signature: `2tMYYz4YWDiqMWF4H34t1oz5PRfvMfQZbXKUM6ZpK2SocmKrik2pbbx4k734LTe2mEgi5WvqLwMAZAzUqYuBD3uv`

This census does NOT add Kamino V2 or any other liquidation-like instruction. Any future class requires its own historical authority.

## Frozen first census chunk

Half-open interval:
`[2023-11-17T14:48:24Z, 2023-11-18T00:00:00Z)`

Rationale:
- the lower endpoint is the already RAW-verified earliest successful event;
- the upper endpoint is the next UTC-day boundary;
- no market outcome was viewed to select the interval.

## Preserved source input

Use the existing first-success continuation artifact as the signature source:
- parent run: `35704794316`
- artifact: `10686881756`
- artifact name: `dls-kamino-rpc-first-success-v01b`
- artifact SHA256: `15097adc6e833edfc99ab11f24c6c4057752b2df7c5de831567bdc6cc01ecf14`

The artifact contains the already-preserved `getSignaturesForAddress` pages that crossed this interval. The census MUST reconstruct the complete signature queue from those pages rather than re-enumerating the chain.

## Queue rules

1. Read every `signatures_page_*.json` in the preserved artifact.
2. Require a structurally valid JSON-RPC result list.
3. Keep rows whose `blockTime` is inside the frozen half-open interval.
4. Require unique signatures.
5. Persist signature, slot, blockTime and signature-level err.
6. Sort oldest -> newest by `(blockTime, slot, signature)`.
7. The known first-success signature MUST be present.
8. Hash and persist the complete queue before RAW adjudication.

## RAW adjudication

For every queued signature, including failed attempts:
- fetch `getTransaction` from the official public Solana RPC;
- preserve the raw JSON-RPC response bytes;
- require returned slot/signature status consistency;
- inspect top-level and inner/CPI instructions;
- match only exact program + discriminator;
- do not decode instruction amounts.

Classification:
- exact match with RAW `meta.err == null` => authoritative realized liquidation event;
- exact match with RAW `meta.err != null` => `LIQUIDATION_ATTEMPT_FAILED_NOT_REALIZED`;
- no exact match => non-candidate program transaction;
- missing/null/mismatched RAW => fail closed.

If a transaction contains multiple exact matching liquidation instructions, fail closed for schema ambiguity rather than silently deduplicating.

## Required outputs

- deterministic signature queue + SHA256;
- complete per-signature adjudication ledger;
- realized-event ledger;
- failed-attempt ledger;
- source anomaly ledger if any;
- chunk receipt with counts, time bounds, artifact lineage and RAW response hashes;
- first realized event must reconcile exactly to the already closed first-success boundary.

## Durability

RAW processing checkpoints every 250 signatures. A restart must resume from the persisted queue/index without changing ordering or classification.

## Firewall

prices=false; returns=false; pnl=false; direction=false; market_outcomes=false; event_size_threshold_tuning=false; protocol_selection_from_outcomes=false; protected_2025_2026_market_outcomes=false; live_trading=false; orders=false; wallets=false; exchange_mutation=false; paid_source=false; account_creation=false; merge_main=false.
