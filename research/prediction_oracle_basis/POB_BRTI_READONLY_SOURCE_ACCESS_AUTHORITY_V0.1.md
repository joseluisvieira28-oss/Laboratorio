# POB-BRTI-READONLY-SOURCE-ACCESS-001 — PRE-ACCESS AUTHORITY V0.1

Date: 2026-09-27
Parent: PREDICTION-ORACLE-BASIS-001
Hourly child: POB-HOURLY-STRIKE-BINANCE-CFRTI-001
Branch: prediction-oracle-basis-v0.1
Status: FROZEN_PRE_ACCESS / READ_ONLY / AUTHENTICATED_SOURCE_NOT_YET_EXECUTED

## 1. Trigger

The hourly source/transport phase closed as:

SOURCE_FEASIBILITY_PARTIAL_PASS / HOURLY_SOURCE_TRANSPORT_PASS / BRTI_REFERENCE_ACCESS_BLOCKED

Controlling evidence:
- source-shape run 36339166888 = PASS
- synchronized public transport run 36341997042 = PASS, 10/10 bundles, max bundle span 616 ms
- Kalshi public event live-data run 36342299593 = PUBLIC_REFERENCE_UNPROVEN
- hourly source closeout commit e52f96be52d82a4a7928294da966d5b4af43f002

No economic outcome has been opened.

## 2. Exact source route

First-party Kalshi documentation defines a CF Benchmarks REST passthrough using existing Kalshi API credentials.

Frozen request:
GET https://external-api.kalshi.com/trade-api/v2/cfbenchmarks/values?id=BRTI

Frozen signing path:
 /trade-api/v2/cfbenchmarks/values

The query string is NOT included in the signature.

## 3. Authentication contract

Standard Kalshi request headers:
- KALSHI-ACCESS-KEY
- KALSHI-ACCESS-TIMESTAMP
- KALSHI-ACCESS-SIGNATURE

Signature message:
timestamp_ms + "GET" + "/trade-api/v2/cfbenchmarks/values"

Signature:
RSA-PSS with SHA-256, MGF1 SHA-256 and salt length equal to SHA-256 digest length; base64 encoded.

## 4. Credential handling

Future authenticated execution may consume only legitimate operator-provided credentials stored as protected runtime secrets:
- KALSHI_API_KEY_ID
- KALSHI_PRIVATE_KEY_PEM

Never:
- print either secret;
- serialize either secret into artifacts;
- commit either secret;
- send them in query parameters;
- infer/guess credentials;
- create or rotate API keys;
- call any order, portfolio, balance, position, fill, transfer, RFQ or mutation endpoint.

The private key must exist only in memory or an ephemeral chmod-0600 temporary file and must be deleted before process exit.

## 5. Current authorized implementation phase

Authorized NOW:
- implement request signing;
- synthetic RSA self-test;
- parser/schema test on synthetic fixtures;
- dry-run URL/path/header-name verification;
- credential-presence detection without revealing values;
- fail-closed receipts.

NOT authorized NOW:
- real authenticated Kalshi request;
- BRTI numeric-value acquisition;
- economics;
- market-quote comparison;
- PnL;
- orders or account reads.

A future real source probe requires a separate explicit activation receipt created after legitimate credentials are configured.

## 6. Future real-source PASS contract — frozen now

When separately activated, exactly ONE initial source request may be made to the frozen BRTI endpoint.

Persist:
- request start/finish UTC;
- HTTP status;
- content-type;
- response byte count;
- raw response SHA256;
- top-level/schema key paths;
- whether a BRTI identity field is present;
- whether a point-in-time timestamp is present;
- whether at least one finite numeric index value is present.

Do NOT persist the numeric BRTI value in the initial source-access receipt.

Classifications:
- BRTI_SOURCE_ACCESS_PASS
- BRTI_CREDENTIAL_ABSENT
- BRTI_AUTH_OR_ENTITLEMENT_BLOCKED
- BRTI_SOURCE_SCHEMA_UNPROVEN
- BRTI_SOURCE_TECHNICAL_FAILURE

PASS requires HTTP 2xx machine-readable response plus BRTI identity + timestamp + finite numeric-value presence.

## 7. Hard firewall

This authority does not authorize:
- prediction-market quote economics;
- settlement outcome reads;
- arbitrage-spread calculations;
- strategy PnL;
- best strike/time selection;
- threshold tuning;
- account/balance/portfolio reads;
- orders;
- capital;
- exchange mutation;
- live trading;
- main merge.

## 8. Next scientific boundary

Only after BRTI_SOURCE_ACCESS_PASS may a separate prospective economic protocol be frozen.

That later protocol must freeze before collecting economic evidence:
- exact 1-cent boundary state mapping;
- synchronized books;
- BRTI/Binance reference-state mapping;
- per-market fee provenance;
- depth/capacity;
- one-leg execution stress;
- timestamp-shift placebo;
- sample minimum;
- inference;
- untouched prospective evidence;
- Diamond Test gates.

This authority unlocks source provenance only. It cannot create an edge verdict.
