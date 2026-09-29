# DEFI-LIQUIDATION-SHOCK-001 — SAVE11 SAME-TX PROGRAM SAMPLE FREEZE V0.1

Date: 2026-09-29
Status: FROZEN SOURCE-ONLY / NO MARKET OUTCOMES

Population source:
- canonical field partition save11-202407
- classification FIELD_ENRICHMENT_PARTITION_PASS
- population count 1,572

Sample:
- rank every canonical event by SHA256(signature + "|" + canonical JSON instructionAddress)
- take first 64
- no price/return/outcome field participates in selection

For each sample recover the exact successful transaction and enumerate every instruction program in canonical instructionAddress order.

This probe asks only whether same-transaction program evidence exists that could support a later source-semantic direction rule.

It does NOT infer BUY/SELL from program presence alone.

Firewall:
prices=false
returns=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
