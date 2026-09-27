# ETH-STAKING-FLOW-001 — V3 STAGE-A CHAINSAFE SERIAL RETRY V0.2.3

Date frozen: 2026-09-27
Status: FROZEN BEFORE NETWORK EXECUTION / SOURCE-ONLY / OUTCOME-BLIND

## Trigger evidence

The previously frozen public Beacon archive matrix V0.1.6 tested:
https://lodestar-mainnet.chainsafe.io

The endpoint did not prove historical-state absence. It returned transport/capacity responses:
- HTTP 429 Too Many Requests
- HTTP 500 QUEUE_ERROR_QUEUE_MAX_LENGTH

Therefore one bounded transport-only retry is authorized.

## Frozen endpoint

Only:
https://lodestar-mainnet.chainsafe.io

No additional provider or endpoint may be added after execution begins.

## Frozen calls

For each target slot S, query exactly:

GET /eth/v1/beacon/states/{S}/validators?status=pending_queued
GET /eth/v1/beacon/states/{S}/validators?status=active_exiting

Count the returned validator objects exactly.

No current-state substitution.
No nearest slot.
No alternate state identifier.
No interpolation.

## Transport policy

Serial requests only.

For each call:
- timeout: 120 seconds
- max attempts: 6
- retry only on 408, 425, 429, 500, 502, 503, 504 or transport timeout
- deterministic backoff after failed attempts: 5, 10, 20, 30, 30 seconds
- no parallelism
- minimum 2 seconds between successful calls

A non-retryable HTTP error is terminal for that control/date.

## Mandatory controls

First query only:

2025-02-24:
- epoch 347738
- slot 11127616
- pending_queued 0
- active_exiting 5
- net -5

2025-03-02:
- epoch 349088
- slot 11170816
- pending_queued 0
- active_exiting 0
- net 0

2025-10-17:
- epoch 400613
- slot 12819616
- pending_queued 48
- active_exiting 55209
- net -55161

3/3 exact required.

If any control cannot be acquired after the frozen retry budget:
SOURCE_ACQUISITION_TECHNICAL_FAILURE.

If any acquired control disagrees:
SOURCE_PROVENANCE_FAILURE.

## Seven missing dates

Only after 3/3 exact controls may query:

- 2025-02-25 — slot 11134816
- 2025-02-26 — slot 11142016
- 2025-02-27 — slot 11149216
- 2025-02-28 — slot 11156416
- 2025-03-01 — slot 11163616
- 2025-10-18 — slot 12826816
- 2025-10-19 — slot 12834016

Every date must return both status counts.

## Splice

Legacy source authority:
GitHub Actions run 35387477455.

Only the seven frozen missing dates may be supplied by V0.2.3.

Final SOURCE_REPLICATION_PASS still requires:
- 601 immutable legacy rows
- 7 exact recovered rows
- 608/608 unique dates through 2026-08-31
- target epoch/unix geometry preserved
- deterministic daily series hash
- no market outcomes.

## Firewall

Source-only.
No ETH/BTC price data.
No signals/threshold evaluation.
No returns/PnL.
No source after 2026-08-31.
No market after 2026-09-08.
No live trading/orders/wallet/exchange mutation.
No main merge.
No tuning.

Stage B remains closed unless SOURCE_REPLICATION_PASS.
