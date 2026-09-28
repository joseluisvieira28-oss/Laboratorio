# POB-HOURLY-SYNC-CAPTURE-001 — TRANSPORT REMEDIATION AUTHORITY V0.1

Date: 2026-09-27
Parent: PREDICTION-ORACLE-BASIS-001
Branch: prediction-oracle-basis-v0.1
Status: FROZEN_PRE_RERUN / SOURCE_TRANSPORT_ONLY / OUTCOME_BLIND

## Trigger

The first prospective synchronized capture was executed under POB_HOURLY_SYNC_CAPTURE_AUTHORITY_V0.1.

Canonical run:
- GitHub Actions run: 36341635466
- Job: 108682746747
- Artifact: 10938609609
- Scientific firewall: PASS
- Final transport state: SOURCE_TRANSPORT_BLOCKED

Observed transport facts:
- deterministic selected pairs: 3
- required bundles: 10
- complete bundles: 0
- maximum bundle span observed: 291 ms
- maximum allowed bundle span: 3000 ms
- every Polymarket YES/NO CLOB request returned a readable public book;
- every Kalshi public order-book request returned a readable public book;
- Binance api.binance.com BTCUSDT bookTicker returned HTTP 451 from the GitHub hosted runner;
- no matured outcomes were read;
- no economic outputs were computed;
- no future-nearest joins or silent imputations occurred.

This is a source transport failure, not a scientific or economic result.

## First-party transport basis

Binance documents data-api.binance.vision as a market-data-only base endpoint for public Spot market-data REST routes. The frozen request remains GET /api/v3/ticker/bookTicker?symbol=BTCUSDT and requires no authenticated trading capability.

## Authorized remediation

Exactly one source-transport substitution is authorized:

FROM:
https://api.binance.com/api/v3/ticker/bookTicker

TO:
https://data-api.binance.vision/api/v3/ticker/bookTicker

Everything after the host is unchanged.

## Frozen invariants

No change is authorized to:
- parent or child economic mechanism;
- pair population;
- earliest-resolution selection;
- minimum / median_floor / maximum strike selection;
- selected pair count requirement = 3;
- snapshot count = 10;
- interval = 15 seconds;
- concurrent acquisition;
- max bundle span gate = 3000 ms;
- Polymarket routes;
- Kalshi routes;
- reference identities;
- 1-cent boundary classification;
- outcome firewall;
- future-nearest join rule;
- imputation rule;
- any future economic rule.

## BRTI diagnostic

The BRTI machine-feed diagnostic remains non-economic and independent of the synchronized book-capture gate.

The first run returned a non-machine-readable response from the direct CF Benchmarks API route without credentials. No credential guessing, purchase, authentication or entitlement escalation is authorized by this remediation.

Do not alter the BRTI diagnostic classification merely to obtain a more favorable label in this rerun.

## Rerun adjudication

The unchanged synchronized capture gate is rerun once after the host substitution.

Possible states remain:
- SOURCE_TRANSPORT_READY
- SOURCE_TRANSPORT_READY_BRTI_AUTH_BLOCKED
- SOURCE_TRANSPORT_READY_BRTI_ROUTE_UNRESOLVED
- SOURCE_TRANSPORT_BLOCKED

No state is evidence of an economic edge.

## Forbidden

No PnL, package-spread, expected value, arbitrage-profit, win-rate, outcome read, order, authenticated trading endpoint, capital, exchange mutation, leverage, wallet action, main merge or post-result scientific tuning.
