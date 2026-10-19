# CRYPTO LAB — FUNDING HUNTER V03 OKX BTC DUAL PERPETUAL REAL L2 PRE-READ FREEZE

2026-10-19 UTC. **Frozen before inspecting the 2025-06-02 uploaded archives or any contained historical orderbook quote.** Reuse V02, PR #253, no strategy/outcome retuning. Both archives supplied by operator privately:
- BTC-USDT-SWAP-L2orderbook-400lv-2025-06-02.tar.gz — USDT-settled linear BTC perpetual.
- BTC-USD-SWAP-L2orderbook-400lv-2025-06-02.tar.gz — USD-notional inverse, coin-margined BTC perpetual.

**The question for V03 is strictly quote/source compatibility, NOT funding economics, edge, broker orders, or forward evidence.**

## Fixed data and exact causal probes BEFORE source inspection

Require official archive original filename, valid gzip-TAR, exactly one regular .data member in expected instrument/day; no path traversal, bounded event line bytes, JSON event `{instId,action,ts,asks,bids}`, `[price,contract_count,order_count]` per level, full first snapshot, chronological incrementals, quantity-zero deletion, non-crossed books, exactly 400 levels of each side at each selected probe, freshness <=2,000 ms, strictly prior quotes only. If format differs, publish schema blocker before adapting; fail-closed. No de-dup or reordering of source events. No sequence ids in observed historical 2023 OKX files; 2025 must be checked separately; missing continuity metadata = NO LOSSLESS CONTINUITY PROOF even with fresh quotes. SHA256 local user archive != official OKX signed digest.

Three **prespecified identical UTC probe times**, independent of source prices or funding outcomes:
- 2025-06-02 **00:05:00.000 UTC** (matches V01 daily hypothetical entry hour).
- 2025-06-02 **12:05:00.000 UTC** (midday neutral diagnostic).
- 2025-06-02 **23:55:00.000 UTC** (near-day-end diagnostic, NOT an exit for V01 which is next day 00:05 UTC).
All probes nearest genuine observed source book at or before exact time; never look ahead. If any missing, no success for complete series. Files are one day only; 2025-06-03 required for the original 24h exit. Never infer 24h fills or 2025 full period.

## What to publish from each book

Exact source time, age, raw best BID, raw best ASK, raw number of contracts at top BID/ASK, full L2 400 levels each side, raw total contract quantity on each side, spread bps within each instrument, event counts, first/latest timestamps, max adjacent timestamp gap, number of snapshots and source sequence continuity status. Compare simultaneous observable BTC-USD quote vs BTC-USDT quote **only** as separate market references; the difference contains USD/USDT FX/premium/mark differences and is not free basis-profit. Instrument contract `ctVal`, `ctValCcy`, `lotSz`, tick size in force **on 2025-06-02** MUST be proven from dated exchange spec before converting raw contracts into BTC/USD quote value or claiming 1 BTC executable. If not: raw size only; no sizing, impact or VWAP economic claim. No attempt to fabricate historical metadata from current instruments.

Native BTC inverse payout and coin collateral cannot be equated to linear USDT; even equal initial USD notionals need contract/lot proof and dynamic delta hedge, separate maintenance margins and coin/collateral FX.

The V02 manually retrieved June 2025 funding CSVs for both formats, header `instrument_name,funding_rate,funding_time` with **no settlement mark price**. Do NOT open funding outcomes or calculate any economics in V03. If completed, scientific verdict must be `REAL_2025_TWO_BOOKS_RECONSTRUCTED_QUOTE_ONLY`, never a funding strategy candidate. If malformed/stale/incomplete: `SOURCE_BLOCKED` with exact reason.

Privacy: actual source archives remain only local in conversation; **NEVER upload/commit the raw .tar.gz or reconstructed L2 rows to GitHub**. GitHub may contain ONLY a derived sanitized receipt / schema-based code/tests using synthetic dummy fixtures. No 2026 protected holdout read, no exchange credentials/keys/accounts, orders, leverage/live trading, money, merge into main or user Windows service modifications.
