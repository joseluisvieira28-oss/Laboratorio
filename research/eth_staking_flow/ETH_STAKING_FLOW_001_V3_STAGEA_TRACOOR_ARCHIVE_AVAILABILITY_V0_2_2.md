# ETH-STAKING-FLOW-001 — V3 STAGE-A TRACOOR ARCHIVE AVAILABILITY V0.2.2

Date frozen: 2026-09-27
Status: FROZEN BEFORE NETWORK EXECUTION / SOURCE-METADATA ONLY / OUTCOME-BLIND

## Purpose

Test whether the official ethPandaOps Tracoor mainnet service retains exact historical
BeaconState snapshots at the already-frozen Stage-A control and missing target slots.

This stage queries state metadata only. It does NOT download SSZ state bytes and does not
open queue counts or market outcomes.

## Official source

Service:
https://tracoor.mainnet.ethpandaops.io

API route documented by the public ethPandaOps/tracoor code:
POST /v1/api/list-beacon-state

Download route, NOT authorized in this availability stage:
GET /download/beacon_state/{id}

## Exact frozen slots

Controls:
- 2025-02-24 epoch 347738 — slot 11127616
- 2025-03-02 epoch 349088 — slot 11170816
- 2025-10-17 epoch 400613 — slot 12819616

Missing dates:
- 2025-02-25 epoch 347963 — slot 11134816
- 2025-02-26 epoch 348188 — slot 11142016
- 2025-02-27 epoch 348413 — slot 11149216
- 2025-02-28 epoch 348638 — slot 11156416
- 2025-03-01 epoch 348863 — slot 11163616
- 2025-10-18 epoch 400838 — slot 12826816
- 2025-10-19 epoch 401063 — slot 12834016

## Frozen request

For each exact slot, POST:
{
  "network": "mainnet",
  "slot": <exact slot>,
  "pagination": {"limit": 100, "offset": 0, "order_by": "fetched_at ASC"}
}

Record only:
- HTTP status/content type
- response SHA256/byte length
- number of state metadata records
- state id
- node
- slot
- epoch
- state_root
- node_version
- beacon_implementation
- fetched_at

No SSZ body is opened in V0.2.2.

## Availability classification

TRACOOR_EXACT_STATE_ARCHIVE_AVAILABLE if:
- all 10 exact slots return at least one state metadata record with slot exactly equal to target;
- all returned records identify network mainnet;
- for every slot all retained states agree on state_root, or disagreement is preserved and classified provenance failure.

TRACOOR_ARCHIVE_PARTIAL if at least one but not all exact slots has retained state metadata.

TRACOOR_ARCHIVE_UNAVAILABLE if 0/10 exact slots are retained.

SOURCE_PROVENANCE_FAILURE if metadata for the same exact slot contains conflicting state roots.

SOURCE_ACQUISITION_TECHNICAL_FAILURE for transport/schema failure.

A metadata availability PASS does not itself change Stage A. It only permits a separately
frozen SSZ retrieval/decoding/equivalence stage.

## Firewalls

No SSZ state body download.
No validator status counts.
No signal evaluation.
No ETH/BTC market data.
No returns/PnL.
No source beyond 2026-08-31.
No live trading/orders/wallets/exchange mutation.
No main merge.
No post-outcome tuning.
