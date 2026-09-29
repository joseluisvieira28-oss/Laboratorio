# DEFI-LIQUIDATION-SHOCK-001 — KAMINO SAME-TX PROGRAM PARTITION CENSUS FREEZE V0.1

Date: 2026-09-29
Status: FROZEN SOURCE-ONLY / NO MARKET OUTCOMES

Canonical source partition:
- kamino-202311
- FIELD_ENRICHMENT_PARTITION_PASS
- 49 realized successful events

Census all 49 events. No sampling.

For each event:
- recover exact successful transaction by signature;
- match exact Kamino instruction by programId + instructionAddress;
- enumerate all same-transaction instructions in canonical instructionAddress order;
- report program IDs before/at/after liquidation.

Program presence alone does not assign BUY/SELL.
This is a source-feasibility census for later semantic classification.

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
