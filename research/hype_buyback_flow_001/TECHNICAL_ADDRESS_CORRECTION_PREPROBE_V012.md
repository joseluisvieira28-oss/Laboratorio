# HYPE-BUYBACK-FLOW-001 — FAIL-CLOSED SOURCE ADDRESS CORRECTION V0.1.2 (PRE-REPROBE)
Date: 2026-10-10 UTC
Status: TECHNICAL ERROR CORRECTION ONLY. NO OUTCOMES. NO PROMOTION.

## Root cause independently rechecked against OFFICIAL Hyperliquid docs
Exact official Assistance Fund system address is `0xfefefefefefefefefefefefefefefefefefefefe` — **42 characters** (0x + 20 FE bytes).
Official authoritative source: https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees
The initial `source_gate_v01.py` had a truncated 36-character (17 FE-byte) pseudoaddress. The secondary `transport_diag_v011.py` had a truncated 40-character (19 FE-byte) pseudoaddress. Both fail the documented Ethereum-format 42-character address contract; the 422 responses are *compatible* with this bad schema (not proof of server behavior for the corrected address). This was an experiment/operator implementation error, **not evidence of absence of purchases**. Prior `SOURCE_BLOCKED` was premature as a conclusion about the correct official address.

## Correction boundary
- Allow only replacement of the address constants with the exact 42-character official system address and add a failing-on-bad-address synthetic regression; retain all other scientific gates, source lookback and immutable prior failed evidence as-is.
- Transport-v011 requests are the same minimal public-only A/B/C variants. Previously incorrect-address results remain archived; corrected outputs are a NEW canonical run.
- Permitted extra read-only case: `{"type":"spotClearinghouseState","user":official_address}` to verify public HYPE token balance separately from executions. Any balance changes, if present, are NOT equated with buys or fills.
- Observe HTTP response, store raw SHA256, log timestamp/source fields, verify AF buy `tid`, `side`, `coin`, and sample gaps. Any HTTP 200 or positive count is SOURCE TRANSPORT only; not a 90-day historical source PASS.
- Do not fetch HYPE future prices or compute response returns. Do not initiate a new trading plan, optimized buy/sell rule, historical market backtest, closed experiment rescue, or unseal protected outcomes.
- No private credentials, private accounts, wallets, money, AWS requester-pays, exchange mutation, trading, or Render.

## Pre-correction evidence pointers (retained)
- closeout commit `49f98add57469fa6afc4e11e1a64ab67f80a2448`
- transport run `38040421803`, head `70a7c3a8fccde02e78d2b993e84c0c408e35a7b7`, artifact `11665551811`, ZIP SHA256 `471b224ce8452373fec1761a5d7a1c23c327697770f5ccc55d52cfaed1838ee6`.
- Original SOURCE_ONLY freeze remains immutable; this note is a disclosed narrowly scoped typo correction, written before any corrected-address request.
