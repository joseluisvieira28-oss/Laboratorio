# POB-HOURLY-SYNC-CAPTURE-001 — PRE-CAPTURE AUTHORITY V0.1

Date: 2026-09-27
Parent: PREDICTION-ORACLE-BASIS-001
Child source-shape authority: POB-HOURLY-STRIKE-BINANCE-CFRTI-001
Status: FROZEN_PRE_CAPTURE / OUTCOME_BLIND / RESEARCH_ONLY
Branch: prediction-oracle-basis-v0.1

## 1. Trigger evidence

Canonical source-shape run:
- GitHub Actions run: 36339166888
- Artifact: 10938710472
- Classification: SOURCE_SHAPE_PASS_MATCHED_HOURLY_STRIKE_TIME
- Kalshi future candidates: 268
- unique future resolution times: 2
- matched exact time + nominal strike pairs: 20
- matched pairs with readable public book routes: 20
- matured outcomes read: false
- economic outputs computed: false
- future-nearest joins: 0
- silent imputations: 0

This authorizes only a prospective transport/capture validation. It does not authorize economic analysis.

## 2. Question

Can the current matched hourly BTC population be captured synchronously and reproducibly from public read-only endpoints with bounded timestamp skew, while preserving exact contract identity and without opening any matured outcome or computing any cross-venue economics?

Separately: is a machine-readable first-party BRTI value feed accessible without credentials from the tested official route?

## 3. Deterministic pair selection

At capture initialization:

1. enumerate current open Kalshi KXBTCD markets;
2. keep future resolution instants within the next 12 hours;
3. derive the matching Polymarket hourly event slug deterministically from each Kalshi resolution instant;
4. retain only same-time + same-nominal-strike pairs satisfying the already-frozen classification:
   MATCHED_HOURLY_STRIKE_TIME_REFERENCE_DIFF_TIE_1C;
5. select the earliest future matched resolution instant;
6. sort its matched nominal strikes numerically;
7. select exactly three positions: minimum, median using floor((n-1)/2), and maximum; if fewer than three unique pairs exist, capture all unique pairs and classify SAMPLE_SHAPE_INSUFFICIENT_FOR_3_STRIKE_GATE.

No quote, probability, volume, liquidity, spread, outcome or historical performance may influence pair selection.

## 4. Prospective capture schedule

- snapshot bundles: 10
- interval: 15 seconds between bundle starts
- no backfill
- no nearest-future substitution
- no stale-last-trade substitution
- no retry after the workflow's bounded capture window
- all timestamps UTC

For every selected pair and bundle, acquire concurrently:
- Polymarket YES public CLOB book;
- Polymarket NO public CLOB book;
- Kalshi public market order book;
- Binance public BTCUSDT bookTicker as a contemporaneous transport/reference timestamp primitive.

The capture may preserve raw public quote/depth values and sizes.
It may NOT calculate cross-venue spread, package cost, arbitrage profit, expected value, PnL, win rate, optimal strike, best time or trading direction.

## 5. Timing measurements

Each request records:
- request start UTC;
- request finish UTC;
- HTTP status;
- byte count;
- raw SHA256.

Each snapshot bundle records:
- bundle start UTC;
- bundle finish UTC;
- total bundle span milliseconds;
- per-source completion state.

No exchange timestamps may be silently substituted for local acquisition timestamps.

## 6. BRTI route diagnostic

Test only this first-party route without credentials:

https://www.cfbenchmarks.com/api/v1/values?id=BRTI

Record:
- HTTP status;
- content type;
- byte count;
- response SHA256 if any;
- whether a machine-readable BRTI payload is returned.

Do not guess credentials.
Do not use secrets.
Do not authenticate.
A 401/403/authentication challenge is classified BRTI_MACHINE_FEED_AUTH_REQUIRED, not scientific failure.

Public documentation establishing that Kalshi settles current crypto contracts from CF Benchmarks RTI remains source-provenance evidence; this diagnostic tests machine feed access only.

## 7. Gate

SYNC_CAPTURE_PASS requires ALL:
1. at least 3 deterministic selected pairs;
2. 10/10 snapshot bundles complete;
3. every selected pair has all three prediction-market book routes readable in every bundle;
4. Binance BTCUSDT reference transport readable in every bundle;
5. zero future-nearest joins;
6. zero silent imputations;
7. zero matured-outcome reads;
8. zero economic outputs;
9. maximum bundle acquisition span <= 3000 ms;
10. immutable receipt with hashes.

BRTI feed access is adjudicated separately:
- BRTI_MACHINE_FEED_PUBLIC_PASS
- BRTI_MACHINE_FEED_AUTH_REQUIRED
- BRTI_MACHINE_FEED_TECHNICAL_FAILURE

Permitted combined states include:
- SYNC_CAPTURE_PASS / BRTI_MACHINE_FEED_PUBLIC_PASS
- SYNC_CAPTURE_PASS / BRTI_MACHINE_FEED_AUTH_REQUIRED
- SYNC_CAPTURE_FAIL / <BRTI state>

A capture PASS does not prove edge and does not authorize economic analysis.

## 8. Forbidden

- matured market outcome reads;
- PnL/profitability/EV/arbitrage-spread calculation;
- quote-based pair selection;
- strike/time optimization;
- authenticated trading endpoints;
- orders;
- capital;
- exchange mutation;
- leverage;
- wallet actions;
- main merge;
- post-result gate edits.

## 9. Next decision

Only after this authority is executed once may a closeout decide whether the transport layer is:
- SOURCE_TRANSPORT_READY;
- SOURCE_TRANSPORT_READY_BRTI_AUTH_BLOCKED;
- SOURCE_TRANSPORT_BLOCKED.

Any later economic hypothesis requires a new prospectively frozen authority.
