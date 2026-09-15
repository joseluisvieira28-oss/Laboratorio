# MSEL-001 — PILOT RAW DATA SCHEMA V0.1

Status: FROZEN PRE-OUTCOME

## Principle

Raw evidence and derived features are different layers. Never overwrite raw RPC payloads. Every raw page is stored unchanged/canonically serialized with SHA-256 before parsing. Derived tables must retain source signature/slot references.

## A. Launch table — one row per CREATE

Required fields:

- `cohort_rank`
- `slot`
- `block_time`
- `transaction_index` (or explicit missing flag)
- `signature`
- `instruction_scope`
- `instruction_index`
- `mint`
- `bonding_curve`
- `origin_creator`
- `tx_user`
- `fee_payer`
- `name`
- `symbol`
- `uri`
- `same_tx_pump_buy`
- `origin_creator_eq_tx_user`
- `origin_creator_eq_fee_payer`
- `historical_idl_commit`
- `raw_page_sha256`

No future outcome columns are permitted in the launch table before feature freeze.

## B. Trade-event table — all Pump buys/sells through snapshot

Required fields:

- `mint`
- `slot`
- `block_time`
- `signature`
- `transaction_index`
- `instruction_scope/index`
- `side` (`buy`/`sell`)
- `user`
- `fee_payer`
- `token_amount_raw`
- `quote_amount_raw`
- `virtual_token_reserves_after` if event/schema supports it
- `virtual_sol_reserves_after` if event/schema supports it
- `real_token_reserves_after` if available
- `real_sol_reserves_after` if available
- `fee fields` only if directly reconstructible under historical regime
- `same_tx_as_create`
- `known_protocol_account_flag`

Events after the evaluated snapshot cannot enter that snapshot's features.

## C. Token-transfer table — target mint, launch to T+5

Required fields:

- `mint`
- `slot`
- `block_time`
- `signature`
- `source_owner`
- `destination_owner`
- `source_token_account`
- `destination_token_account`
- `amount_raw`
- `transfer_type`
- `source_evidence`

Transfers are required for holder-state closure. Failure to resolve owner or amount is explicit missingness, not zero.

## D. Funding-edge table — PIT only

Required fields:

- `child_wallet`
- `funder_wallet`
- `funding_asset`
- `amount_raw`
- `slot`
- `block_time`
- `signature`
- `edge_before_t1`
- `edge_before_t3`
- `edge_before_t5`
- `funder_degree_prior_only`
- `known_service_hub_flag`
- `confidence_tier`

No edge after the snapshot may be used retroactively.

## E. Snapshot-state table — T+1/T+3/T+5

One row per mint per snapshot:

- snapshot timestamp/slot boundary
- transaction count
- buy count / sell count
- unique buyers / unique sellers
- external unique buyers
- creator/seed activity
- gross buy notional
- gross sell notional
- external net inflow
- curve reserve state
- curve progress
- holder count after transfer closure
- top-1/top-3/top-5/top-10 holder share, if closure passes
- HHI/Gini, if closure passes
- creator-cluster-adjusted concentration variants
- same-funder / same-slot / Jito-tip proxy metrics
- metadata prior-match counts
- data-completeness flags

## F. Evidence completeness flags

Every snapshot must carry:

- `trade_reconstruction_pass`
- `transfer_closure_pass`
- `funding_graph_pass`
- `metadata_pit_pass`
- `curve_state_reconciliation_pass`
- `ordering_pass`
- `schema_pass`

If a required family fails, associated features are unavailable. Do not impute with favorable values.

## G. Feature freeze hash

Before outcomes are opened:

1. sort launch rows by frozen cohort rank;
2. sort event tables by slot / transaction index / signature / instruction index;
3. serialize normalized feature matrix deterministically;
4. record SHA-256 and git commit;
5. write a feature-freeze receipt with all source hashes.

Only after that receipt exists may the predefined outcome collector run.

## H. Forbidden pre-outcome columns

Before feature freeze, the feature-source layer must not contain:

- return after T+5;
- max future price;
- min future price;
- graduation after T+5;
- future liquidity;
- later creator success/failure not completed before launch;
- later wallet profitability;
- future social virality;
- human labels informed by later price action.
