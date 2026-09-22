# DEFI-LIQUIDATION-SHOCK-001 — SOLANAFM RENDER SOURCE PROBE CLOSEOUT V0.2

Date: 2026-09-22
Status: **INDEXED_ROUTE_ACCESS_BLOCKED**

## Independent runtime re-test

GitHub-hosted source probe previously returned HTTP 502 for all four frozen program-address queries.

The same frozen source-only query was then exposed through the canonical Render Frankfurt runtime and executed through GitHub Actions run **35716445956**.

Results:

- Kamino Lend — HTTP 502 — transport/schema pass: false
- marginfi v2 — HTTP 502 — transport/schema pass: false
- Drift v2 — HTTP 502 — transport/schema pass: false
- Save/Solend — HTTP 502 — transport/schema pass: false

Accessible protocols: **0/4**.

Machine classification:
`INDEXED_ROUTE_ACCESS_BLOCKED`

## Adjudication

SolanaFM is not a defensible current indexed source for this lab. The failure reproduced across both GitHub-hosted execution and the canonical Render Frankfurt runtime, so no further runtime-routing rescue is authorized for this endpoint family.

This is a source-route closeout only. It is NOT:
- SOURCE_DATA_PASS;
- a scientific mechanism failure;
- NO_EDGE;
- a liquidation-census result.

The previously verified 23/23 raw historical sample remains valid and unchanged.

## Remaining indexed reopening route

Solscan Enhanced remains a frozen candidate route because its documented endpoint exposes time/program/status/instruction-discriminator filters. The existing credential gate returned `AUTH_REQUIRED_NOT_EXECUTED`; no API key was fabricated, copied or exposed.

## Firewalls

prices=false
returns=false
pnl=false
direction=false
market_response=false
first_success_boundary_adjudicated=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
capital=false
main_merge=false
