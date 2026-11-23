# BINANCE-007C — NO-MARKET-DATA PROVIDER CATALOG FORENSICS

Frozen 2026-11-23. Purpose: independently diagnose two SOURCE_BLOCKED preregistered provider paths in BINANCE-007 PR #380 and BINANCE-007B PR #381. No price, order book or trade file download is authorized in this diagnostic.

Only query anonymous public Hugging Face dataset INFORMATION and TREE JSON for:
- MaximumLeverage/crypto-lob-stream
- Goooddy/crypto-lob-stream

Inspect the ACTUAL returned tree JSON shape/types/paths and count (including whether recursive listing was truncated or directories are returned instead of file nodes). Enumerate limited catalog example paths and candidate real BTCUSDT 2026 month listings, with original response SHA256 and immutable provider revision. Metadata not a substitute for L2 source quality. Do not infer profitability or alpha. If catalog inspection reveals that BINANCE-007/007B mistakenly parsed API response, document error precisely, and any subsequent full historical source read must be separately approved/frozen without overwriting prior failed run receipts.

One GitHub public standard runner, read-only anonymous public metadata GETs only, max 2MB JSON per response, no retries. No source ZIP/Parquet downloads, no account or billing, no paid endpoints, no orders, no edits to BINANCE-004/005/006/007/007B, main untouched, PR DRAFT.
