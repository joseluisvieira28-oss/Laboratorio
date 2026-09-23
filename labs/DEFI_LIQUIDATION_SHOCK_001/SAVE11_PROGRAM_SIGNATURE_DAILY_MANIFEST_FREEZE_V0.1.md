# DEFI-LIQUIDATION-SHOCK-001 — SAVE11 PROGRAM SIGNATURE DAILY MANIFEST FREEZE V0.1

Date: 2026-09-23
Status: SOURCE-TRANSPORT INDEX ONLY / OUTCOME-BLIND / FAIL-CLOSED

Purpose:
Convert the already-preserved Save/Solend program-signature crawl into a compact UTC-day manifest for deterministic queue reconstruction.

Program:
`So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo`

Frozen source lineage:
- run `35715830047`
- artifact `10690805384`
- artifact name `dls-save11-first-success-rpc-v01`
- artifact SHA256 `e72c22a7164ba8787c03201a3d7b2eb1a42a6ffc4384d3dcb8e80695aa9e8c7c`

Input `signatures_page_*.json` is consumed in ascending page number and original row order, newest -> oldest.

For every UTC day, persist:
- row count;
- signature-level success/failed counts;
- canonical queue SHA256 over `signature,slot,blockTime,err`, sorted oldest -> newest;
- immediate newer and older adjacent program signatures where available;
- an anchor-pair-ready flag.

UTC days with zero program signatures between two observed program signatures must also be materialized as explicit zero-row entries.

This manifest does NOT classify liquidation instructions. It is transport/source indexing only.

Integrity:
- non-null blockTime required;
- source order must be globally non-increasing in blockTime;
- within-day signatures unique;
- malformed pages fail closed.

No prices, amounts, returns, PnL, direction, market outcomes, liquidation classification, live trading, orders, wallets, exchange mutation, paid sources, account creation or main merge.
