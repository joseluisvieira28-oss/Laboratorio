# PREDICTION-SETTLEMENT-RV-001 — SYNCHRONIZED CAPTURE SMOKE AUTHORITY V0.1

Date: 2026-09-27
Status: FROZEN_PRE_CAPTURE / SOURCE_ONLY / OUTCOME_BLIND
Lab: PREDICTION-SETTLEMENT-RV-001

## Purpose

Prove that the four required public source legs can be captured prospectively with bounded temporal skew while preserving raw bytes for later source audit and keeping quote values sealed from economic interpretation.

This is a transport/source smoke test, not an economic experiment.

## Frozen eligible target

At run start:
1. enumerate future KXBTCD contracts and deterministic matching Polymarket hourly threshold markets under the already-frozen matcher;
2. group MATCHED_SETTLEMENT_BASIS_PAIR rows by exact UTC resolution instant;
3. retain only resolution instants between T+5 minutes and T+120 minutes;
4. select the earliest eligible resolution instant;
5. capture ALL matched strikes at that resolution.

No selection may use price, spread, depth, probability, volume, liquidity, outcome or expected profitability.

If no group is eligible:
WAITING_ELIGIBLE_EXPIRY.

## Frozen synchronized batch

For every matched pair, launch the following four public GET requests concurrently:
A. Polymarket YES CLOB book;
B. Polymarket NO CLOB book;
C. Kalshi exact-market public orderbook;
D. Coinbase Exchange USDT-USD public ticker.

Each response is preserved byte-for-byte in the artifact.

## Timing definition

For each request:
request_midpoint_utc = started_utc + (finished_utc - started_utc)/2.

Per-pair synchronization skew:
max(request_midpoint_utc) - min(request_midpoint_utc).

Frozen smoke tolerance:
- maximum midpoint skew <= 2.0 seconds;
- each individual request elapsed <= 5.0 seconds.

These values are frozen before the smoke result.

## Schema requirements

Polymarket:
- valid JSON object;
- bids list;
- asks list.

Kalshi:
- orderbook_fp object;
- yes_dollars list;
- no_dollars list.

Coinbase:
- bid;
- ask;
- time.

Level values may be stored in sealed raw bytes but must not be printed or summarized numerically in this phase.

## Smoke PASS

SYNCHRONIZED_CAPTURE_SMOKE_PASS requires:
- >=1 matched pair in the selected expiry;
- all four requests successful for every captured pair;
- all schemas valid;
- all pairs satisfy <=2.0s midpoint skew;
- all individual requests <=5.0s;
- zero future-nearest joins;
- zero silent imputation;
- raw bytes and manifest hashes preserved.

The smoke PASS does NOT satisfy the >=99% prospective schedule coverage gate and therefore does NOT set SOURCE_DATA_PASS=true.

## Stale-source boundary

Native quote timestamps are not assumed to exist on both book APIs.

This smoke records response timing and raw hashes only.
The later multi-observation source gate must add a pre-frozen stale-book detector using repeated raw/book-state identity and source-specific timestamp fields where available.

## Outcome firewall

Forbidden:
- matured contract outcomes;
- PnL;
- package cost;
- arbitrage calculation;
- expected return;
- best strike/hour;
- quote-value reporting;
- economic ranking;
- orders;
- authentication;
- capital;
- exchange mutation;
- merge to main.
