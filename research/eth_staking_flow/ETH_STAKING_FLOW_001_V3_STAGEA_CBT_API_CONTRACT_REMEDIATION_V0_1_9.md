# ETH-STAKING-FLOW-001 — V3 STAGE-A CBT API CONTRACT REMEDIATION V0.1.9

Date frozen: 2026-09-27
Status: FROZEN BEFORE NETWORK EXECUTION / SOURCE-ONLY / OUTCOME-BLIND
Parent: V0.1.5 CBT transition remediation

## Purpose

Resolve a transport/response-contract ambiguity observed in the V0.1.5 public CBT probe.

V0.1.5 received HTTP 200 from the lab proxy for `dim_validator_status`, but the response serialized with no recognized row array. The scientific lifecycle reconstruction remains unchanged. This remediation only determines the currently valid REST path and response envelope for the already-authorized `dim_validator_status` source.

## Frozen endpoints

Probe exactly:

1. `https://lab.ethpandaops.io/api/v1/mainnet/dim_validator_status`
2. `https://lab.ethpandaops.io/api/v1/dim_validator_status`
3. `https://cbt-api-mainnet.primary.production.platform.ethpandaops.io/api/v1/dim_validator_status`

No endpoint may be added after first execution.

## Frozen requests

For each endpoint query only validator_index in {0,1,2} using exact primary-key equality:

- `validator_index_eq=0`
- `validator_index_eq=1`
- `validator_index_eq=2`

with:
- `page_size=20`
- no epoch/date expansion
- no market source
- no signal evaluation.

Record only:
- HTTP status;
- content-type;
- body SHA-256;
- JSON top-level type;
- top-level keys if object;
- row-array field name if identifiable;
- row count;
- field names present in returned rows;
- pagination token presence.

Source row values may be retained in the private workflow artifact for transport debugging but are not scientific outcomes.

## PASS

`CBT_API_CONTRACT_PASS` requires at least one frozen endpoint to return at least one validator lifecycle row for one or more exact validator IDs, with identifiable fields sufficient to map:
- validator_index
- status
- epoch
- epoch_start_date_time
- activation_epoch
- exit_epoch

and a deterministic pagination contract.

If no frozen endpoint exposes usable lifecycle rows:
`SOURCE_ACQUISITION_TECHNICAL_FAILURE`.

This probe cannot emit SOURCE_REPLICATION_PASS by itself.

## Firewall

No ETH/BTC price access.
No signal/threshold evaluation.
No returns/PnL.
No source date after 2026-08-31.
No trading/orders/wallets/exchange mutation.
No main merge.
