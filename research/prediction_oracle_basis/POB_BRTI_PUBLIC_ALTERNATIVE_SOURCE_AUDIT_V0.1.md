# POB — BRTI PUBLIC-ALTERNATIVE SOURCE AUDIT V0.1

Date: 2026-09-28
Parent: PREDICTION-ORACLE-BASIS-001
Branch: prediction-oracle-basis-v0.1
Status: PUBLIC_ALTERNATIVE_NOT_DEFENSIBLE / AUTHENTICATED_OR_LICENSED_SOURCE_REQUIRED

## Question

Can the remaining BRTI source blocker be removed without legitimate Kalshi API credentials or a CF Benchmarks entitlement, while preserving first-party provenance and research governance?

## Sources reviewed

1. CF Benchmarks REST values documentation
   https://docs.cfbenchmarks.com/api/rest/values/

2. CF Benchmarks WebSocket value documentation
   https://docs.cfbenchmarks.com/api/websocket/value/

3. CF Benchmarks BRTI public product page
   https://www.cfbenchmarks.com/data/indices/BRTI

4. CF Benchmarks CFB Oracle page
   https://www.cfbenchmarks.com/cfb-oracle

5. Kalshi API key documentation
   https://docs.kalshi.com/getting_started/api_keys

6. Kalshi authenticated request quick start
   https://docs.kalshi.com/getting_started/quick_start_authenticated_requests

## Findings

### CF Benchmarks direct API

The official REST values endpoint and latest-values endpoint require HTTP Basic authentication.

The WebSocket value feed provides BRTI observations but is an authenticated data service.

Therefore the official machine-readable direct route is not anonymous/public.

### CFB Oracle / on-chain verification

CFB Oracle documents cryptographically verifiable benchmark values and cfb-da-v1 verification material.

However the public CFB Oracle documentation currently describes Ethereum and Ink on-chain verification as launching, while attested values are presently delivered through the API.

This does not establish a currently live anonymous on-chain BRTI source suitable for the frozen point-in-time source gate.

### Public BRTI webpage

The public BRTI page displays an index value and a last-updated timestamp, but it is a website presentation surface, not the frozen machine-readable causal feed.

The same page states that real-time or historical data access for powering a product or service requires licensing/contact with CF Benchmarks.

Its website terms also prohibit automated navigation/retrieval/analysis of website data without prior written permission and state that use/distribution of CF Benchmarks data requires a license.

Accordingly, the lab must not convert the public webpage into an unofficial scraping source.

### Kalshi

Official Kalshi documentation confirms API key creation and RSA-PSS signed authenticated requests.

The existing POB source authority already freezes a read-only Kalshi CF Benchmarks passthrough and prohibits account/order/mutation endpoints.

## Adjudication

PUBLIC_BRTI_ALTERNATIVE_NOT_DEFENSIBLE.

This is not NO_EDGE.

No anonymous/public source discovered in this audit satisfies all of:
- first-party provenance;
- machine-readable point-in-time BRTI identity;
- defensible automated access;
- frozen source-gate requirements.

## Only defensible next routes

A. Legitimate Kalshi API credentials stored as protected secrets, followed by the frozen one-shot read-only BRTI source probe.

or

B. A legitimate CF Benchmarks data entitlement/license providing machine-readable BRTI access.

## Firewall

No BRTI numeric values were collected into research artifacts.
No market quotes were compared.
No matured outcomes were opened.
No economics, PnL, EV or arbitrage calculations were performed.
No orders, account reads, capital, exchange mutation or main merge occurred.

## Scientific state

UNCHANGED:
BRTI_CREDENTIAL_ABSENT / SOURCE_ACCESS_NOT_EXECUTED / NOT_NO_EDGE.
