# CED1D-0031 V0.2C — OFFICIAL MIRROR SOURCE PROBE CLOSEOUT — 2026-09-22

Status: **OFFICIAL_MIRROR_TRANSPORT_BLOCKED**

## Execution

GitHub Actions run: **35688631409**  
Workflow: CED1D-0031 V0.2C Official FAPI Mirror Probe  
Mode: source-only / no forward evidence.

## Result

The exact frozen public endpoint path `/fapi/v1/fundingRate` was probed on the four predeclared official Binance USD-M mirror hosts:

- fapi1.binance.com — HTTP 202 — schema not accepted
- fapi2.binance.com — HTTP 202 — schema not accepted
- fapi3.binance.com — HTTP 202 — schema not accepted
- fapi4.binance.com — HTTP 202 — schema not accepted

Exact-schema accessible hosts: **0/4**.

Machine classification:
`OFFICIAL_MIRROR_TRANSPORT_BLOCKED`

## Adjudication

The existing GitHub-hosted-runner geography/source blocker is not cleared.

Do not:
- activate V0.2B/V0.2C on GitHub-hosted runners;
- treat HTTP 202 as an accepted Binance funding response;
- use a proxy/VPN/geoblock bypass;
- substitute another venue or synthetic funding source;
- backfill the missed forward paths;
- infer NO_EDGE.

The candidate remains scientifically alive but operationally source-blocked for this GitHub runner route.

An objective reopening trigger remains:
1. an explicitly authorized runtime that can access the same official Binance USD-M endpoint under the frozen semantics; or
2. a defensible official Binance archive that preserves the required funding fields/timing.

## Firewall

Forward outcomes computed: false  
Returns/PnL computed: false  
Orders: false  
Live trading: false  
Exchange mutation: false  
Main merge: false
