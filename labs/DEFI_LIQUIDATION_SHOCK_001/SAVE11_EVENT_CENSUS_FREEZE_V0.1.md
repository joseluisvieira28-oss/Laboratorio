# DEFI-LIQUIDATION-SHOCK-001 — SAVE 0x11 EVENT CENSUS FREEZE V0.1

Date: 2026-09-23
Status: FROZEN PRE-EXECUTION / SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED

## Scientific identity

Program:
`So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo`

Authoritative liquidation class:
`LiquidateObligationAndRedeemReserveCollateral`

Frozen native tag:
`0x11`

RAW-verified first-success boundary:
- UTC: `2024-07-19T19:30:52Z`
- slot: `278496102`
- signature: `WdTyQhEUhG2HjQ5LHApW8DU4aLRiKGQ5s8PZYBeoCJ8Acm6tkzqAdL4iasRYnSVnkHTVHTXu7zdgsSmDH8WmQ4L`

This class MUST NOT be back-applied before its supported 2024-07-19 source interval.

## Frozen first census chunk

Half-open interval:
`[2024-07-19T19:30:52Z, 2024-07-20T00:00:00Z)`

## Preserved source input

Use the existing first-success artifact:
- parent run: `35715830047`
- artifact: `10690805384`
- artifact name: `dls-save11-first-success-rpc-v01`
- artifact SHA256: `e72c22a7164ba8787c03201a3d7b2eb1a42a6ffc4384d3dcb8e80695aa9e8c7c`

The artifact already preserves the program signature pages spanning this interval. Do not re-enumerate them.

## Queue rules

1. Read every `signatures_page_*.json` in the preserved artifact.
2. Require valid JSON-RPC result lists.
3. Keep only rows in the frozen half-open interval.
4. Require unique signatures.
5. Persist signature, slot, blockTime and signature-level err.
6. Sort oldest -> newest by `(blockTime, slot, signature)`.
7. Require the known first-success signature to be present.
8. Hash and persist the queue before RAW inspection.

## RAW adjudication

For every queued signature, including failed transactions:
- official public Solana RPC `getTransaction`;
- preserve raw JSON-RPC response bytes;
- require slot/status consistency;
- walk outer and inner/CPI instructions;
- exact program + native tag `0x11` only;
- do not decode liquidation amounts.

Classification:
- exact match + RAW success => authoritative realized event;
- exact match + RAW failure => `LIQUIDATION_ATTEMPT_FAILED_NOT_REALIZED`;
- no exact match => non-candidate program transaction;
- null/missing/mismatch => fail closed.

Multiple exact matches in one transaction => fail closed for schema ambiguity.

## Required outputs

- deterministic queue + SHA256;
- per-signature adjudication ledger;
- realized-event ledger;
- failed-attempt ledger;
- anomaly ledger if needed;
- chunk receipt with exact lineage and RAW hashes;
- first realized event MUST equal the already closed first-success boundary.

## Durability

Checkpoint every 250 signatures. Restart resumes from persisted queue/index without changing ordering.

## Firewall

prices=false; returns=false; pnl=false; direction=false; market_outcomes=false; event_size_threshold_tuning=false; protocol_selection_from_outcomes=false; protected_2025_2026_market_outcomes=false; live_trading=false; orders=false; wallets=false; exchange_mutation=false; paid_source=false; account_creation=false; merge_main=false.
