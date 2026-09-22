# DEFI-LIQUIDATION-SHOCK-001 — SOLANAFM INDEXED SOURCE RECON V0.1

Date: 2026-09-22
Status: SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED

## Purpose

Test whether the documented SolanaFM account-transactions endpoint can provide bounded historical program-address transaction access with server-side UTC filters, avoiding the already-rejected unbounded public-RPC program-address pagination route.

## Frozen probe only

Endpoint family:
`GET https://api.solana.fm/v0/accounts/{program_id}/transactions`

Query:
- utcFrom = 2024-12-15T00:00:00Z
- utcTo = 2024-12-15T23:59:59Z
- limit = 5
- page = 1

Programs:
- Kamino Lend
- marginfi v2
- Drift v2
- Save/Solend

This 24h window is source-recon only. It is not selected by market response and already lies inside the source-only 2021-2024 authority.

## Pass meaning

A HTTP 200 response with parseable transaction metadata only proves that a time-bounded indexed route is technically accessible. It does NOT establish:
- discriminator filtering;
- census completeness;
- historical decoder authority;
- SOURCE_DATA_PASS;
- predictive edge.

## Firewalls

No prices, returns, PnL, direction, market outcomes, event-size selection, protocol winner selection, live trading, orders, wallets, exchange mutation or main merge.
