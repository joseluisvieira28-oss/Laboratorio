# ETH-STAKING-FLOW-001 — V3 STAGE-A FCT_VALIDATOR_BALANCE REMEDIATION V0.2.1

Date frozen: 2026-09-27
Status: FROZEN BEFORE NETWORK EXECUTION / SOURCE-ONLY / OUTCOME-BLIND
Parent state: V3 Stage-A SOURCE_ACQUISITION_TECHNICAL_FAILURE / CBT lifecycle reconstruction provenance failure

## Purpose

Recover the exact seven missing Stage-A source dates from the official ethPandaOps Xatu CBT transformation:
`fct_validator_balance`.

This model is documented upstream as:
- per-epoch validator balance and status;
- one row per validator per epoch;
- directly derived from `canonical_beacon_validators`.

This remediation changes source transport/materialization only. It does not change any economic or signal rule.

## Frozen source

Endpoint:
`https://lab.ethpandaops.io/api/v1/mainnet/fct_validator_balance`

Only this endpoint is authorized.

## Frozen per-epoch count algorithm

For target epoch E and status S in:
- `pending_queued`
- `active_exiting`

query:
- `validator_index_gte=0`
- `epoch_eq=E`
- `status_eq=S`
- `page_size=10000`
- `order_by=validator_index,epoch_start_date_time`

Complete pagination is mandatory.

For every returned row require:
- epoch == E;
- status == requested S;
- epoch_start_date_time == frozen target unix;
- validator_index non-null;
- validator_index unique within the status result.

The count is exactly the number of unique returned validator indices.

No row may be imputed, deduplicated after conflict, or substituted from another epoch.

## Frozen target geometry

Ethereum mainnet genesis timestamp:
1606824023

Epoch duration:
384 seconds

For date D:
target_epoch = ceil((unix_midnight(D)-1606824023)/384)
target_unix = 1606824023 + target_epoch*384

No nearest epoch.
No previous epoch.
No adjacent date.
No interpolation.
No current-state substitution.

## Mandatory controls

Before any missing date may be admitted, the source must reproduce exactly:

2025-02-24:
- epoch 347738
- unix 1740355415
- pending_queued 0
- active_exiting 5
- net_queue -5

2025-03-02:
- epoch 349088
- unix 1740873815
- pending_queued 0
- active_exiting 0
- net_queue 0

2025-10-17:
- epoch 400613
- unix 1760659415
- pending_queued 48
- active_exiting 55209
- net_queue -55161

Any mismatch:
`SOURCE_PROVENANCE_FAILURE`.

## Seven frozen missing dates

Only after 3/3 controls exact:

- 2025-02-25 — epoch 347963
- 2025-02-26 — epoch 348188
- 2025-02-27 — epoch 348413
- 2025-02-28 — epoch 348638
- 2025-03-01 — epoch 348863
- 2025-10-18 — epoch 400838
- 2025-10-19 — epoch 401063

Each must return an exact valid count for both statuses.

## Splice authority

Immutable legacy Stage-A authority:
GitHub Actions run `35387477455`.

Expected legacy valid rows:
601.

Expected frozen missing rows:
7.

Only the seven missing dates may be sourced from this remediation.

Final Stage-A ledger must contain exactly 608 unique dates from 2025-01-01 through 2026-08-31 inclusive, with:
- 601 legacy rows byte/semantic preserved;
- 7 remediation rows;
- exact target epoch/unix geometry;
- no duplicate/outside date;
- deterministic daily-series SHA-256.

## Classification

`SOURCE_REPLICATION_PASS` iff:
- endpoint/schema usable;
- 3/3 controls exact;
- 7/7 missing dates exact and valid;
- legacy 601-row corpus loads without conflict;
- final ledger = 608/608 unique dates;
- all firewalls clean.

Readable control mismatch or inconsistent epoch/status geometry:
`SOURCE_PROVENANCE_FAILURE`.

Transport/schema/pagination/acquisition failure:
`SOURCE_ACQUISITION_TECHNICAL_FAILURE`.

## Stage-B firewall

No ETH/BTC market data.
No signal evaluation.
No threshold evaluation.
No returns/PnL.
No source after 2026-08-31.
No market after 2026-09-08.
No live trading.
No orders.
No wallets.
No exchange mutation.
No main merge.
No post-outcome tuning.

Stage B remains CLOSED unless this exact remediation emits `SOURCE_REPLICATION_PASS`.
