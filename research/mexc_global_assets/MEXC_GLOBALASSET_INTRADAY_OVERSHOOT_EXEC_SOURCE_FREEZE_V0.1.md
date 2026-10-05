# MEXC GLOBAL-ASSET — INTRADAY OVERSHOOT SNAPBACK
## PUBLIC EXECUTION ROUTE SOURCE GATE V0.1

Date: 2026-10-05
Status: FROZEN BEFORE MICROSTRUCTURE OBSERVATIONS

Scientific authority:
- family: MEXC-GLOBALASSET-INTRADAY-OVERSHOOT-SNAPBACK-V1.0
- verdict: ROBUST_API_FEE_SURVIVOR
- outcome run: 37283930479
- mean gross: +20.0820 bps/day
- median gross: +18.2504 bps/day
- mean after frozen 16 bps fee scenario: +4.0820 bps/day
- median after frozen 16 bps fee scenario: +2.2504 bps/day

Purpose:
Validate that the public MEXC Futures market-data route needed for microstructure assessment is accessible for the same 35 contracts, without account access or trading.

Frozen public checks:
- GET public contract detail
- GET public contract depth per symbol
- record request latency
- parse best bid / best ask
- compute top-of-book spread bps
- record available bid/ask level counts
- no order placement
- no authenticated endpoint
- no account read

Route SOURCE PASS per symbol:
- public depth request HTTP 200
- success payload
- non-empty bids and asks
- valid best bid < best ask
- finite non-negative spread

Family route SOURCE PASS:
- 35/35 symbols pass

Important:
This source gate does NOT establish execution feasibility because observations outside 13:30–20:00 UTC are not representative of the frozen strategy session. A separate prospective in-session capture must be frozen before it can support an execution verdict.
