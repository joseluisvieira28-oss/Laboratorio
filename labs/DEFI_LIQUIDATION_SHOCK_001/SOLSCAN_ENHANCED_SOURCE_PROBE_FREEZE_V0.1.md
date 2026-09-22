# DEFI-LIQUIDATION-SHOCK-001 — SOLSCAN ENHANCED SOURCE PROBE FREEZE V0.1

Date: 2026-09-22
Status: SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED

## Documentation basis

Solscan Enhanced account transactions documents:
- raw getTransaction-shaped transaction objects;
- server-side from_time / to_time;
- transaction status;
- program filters;
- exact instruction discriminator filters;
- Free API key authorization on the playground endpoint.

API key transport is the documented HTTP header `token`.

## Frozen feasibility window

UTC window: 2024-12-15 00:00:00 through 2024-12-15 23:59:59.

This is the same already-used source-only validation date and is NOT selected by market response.

## Frozen classes probed

- Save/Solend 0x11: program + prefix 11
- marginfi v2 lending_account_liquidate: d6a997d5fba756db
- Kamino Lend liquidation: b1479abce2854a37
- Drift v2 liquidate_perp: 4b2377f7bf128b02
- Drift v2 liquidate_spot: 6b00802923e5fb12
- Drift v2 liquidate_borrow_for_perp_pnl: a911205acf94d11b
- Drift v2 liquidate_perp_pnl_for_deposit: ed4bc6ebe9ba4b23

## Probe-only adjudication

PASS requires:
- HTTP 200;
- parseable JSON;
- success=true;
- transaction array returned or valid empty result;
- cursor semantics parseable when present;
- no response outside frozen window when blockTime is exposed.

An empty class result is NOT evidence of absence and does not establish a boundary.

## Credential firewall

The code reads `SOLSCAN_API_KEY` only from the process environment.
It must never:
- print the key;
- write the key to evidence;
- commit the key;
- send it as a query parameter.

If the key is absent, classification is:
`AUTH_REQUIRED_NOT_EXECUTED`.

## Scientific firewall

source_data_pass=false
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
merge_main=false
