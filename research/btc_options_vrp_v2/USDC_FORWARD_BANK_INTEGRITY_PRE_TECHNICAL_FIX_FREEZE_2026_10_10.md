# BTC OPTIONS VRP V2 — FORWARD ENTRY BANK SOURCE-INTEGRITY TECHNICAL FREEZE V0.1
**2026-10-10 · before any new Thursday entry source observation.** Branch `audit/vrp-usdc-forward-bank-integrity-2026-10-10` from `btc-options-vrp-v2-forward-2026-10-07`.

## Scope and hard boundaries
Existing authoritative `LINEAR_USDC_FORWARD_ENTRY_SOURCE_BANK_V0.1.md` remains identical: *Thursday 08:05 UTC target*, valid 08:00–08:15 UTC, only public Deribit USDC linear BTC options 14–60 DTE, expiry closest 30 DTE, same strike nearest log moneyness, min 0.01 contracts call and put, one append-only record per date. No PnL, option settlement/forward returns, exchange orders, private account/auth keys, wallet or main merge.

### Problem diagnosed in existing bank code BEFORE outcomes
1. `capture_book()` parses `bids/asks[0]` with raw floats; no finite-positive price and size integrity, no noncrossed book check, and `main()` calls a source_valid gate that checks **bid only**, not ask. A missing option ask can still be labelled `source_valid=true` contrary to the forward source-bank freeze requirement to have complete best bid/ask price+size.
2. Quote freshness is `abs(receive_ms - source_ts)`, allowing **future exchange timestamps** to count as fresh, whereas bank is causal and should reject timestamp > local received time. API is read-only and may exhibit clock skew; skew remains blocked rather than treated as a tradable quote.
3. `existing_dates()` parses JSONL into a SET without detecting **already-duplicated dates** or malformed semantic metadata. A corrupt ledger could accept an additional entry, violating frozen append-only unique-date keys.
4. `main()` writes the record even if quote invalid, as source-only *invalid* receipt; acceptable only when invalid is explicitly marked `source_valid=false` and preserved for audit, NEVER promoted to valid source bank.

## Exactly allowed technical patch
- Define `valid_book_source` as finite positive bid/ask and visible size >=0.01 on selected call+put both sides, noncrossed (`bid<ask`), timestamp 0..30000 ms age with request_start<=response_received. For BTC_USDC-PERPETUAL hedge witness require finite positive best bid+ask, bid<ask, age 0..30000. Perp hedge size must be positive but need NOT be >=0.01 BTC, because its trade unit may not equal option amount and this is a witness, not a simulated hedge order.
- Keep original selection, captured source fields, original source-only outcome seal and Thursday window. Required fields for validity include original min option instrument `min_trade_amount<=0.01`; do not choose a different pair if selected is invalid.
- Append-only `existing_dates()` fails closed on duplicate same `capture_date_utc`, malformed JSON, invalid date strings, unexpected record type, absent source_valid status, and nonexistent expected source receipt for a previously banked date. Test with isolated tmp files (no user data). For compatibility with frozen existing healthy ledger, do not rewrite any prior JSONL row; if stricter validation would flag existing data, fail closed and document.
- Do not write any valid bank entry in this Saturday CI test. CI must use mocked instrument/quotes and synthetic JSONL, at least 12 regressions covering normal, missing ask, crossed/locked, zero size, stale, future timestamps, NaN/Inf, bad min lot, duplicate existing date, malformed JSON, no PnL and unchanged frozen selection.
- Conditional only after isolated CI tests pass: copy *exact* source bank patch and tests to canonical VRP V2 source branch. No workflow-trigger file update and no actual Thursday capture here. Tests cannot open future option settlement / spot paths or performance.
- Operational fact: no `data/vrp_usdc_forward/entry_source_bank.jsonl` on canonical branch at inspection; the prior 2026-10-10 SATURDAY paired quote was a distinct source diagnostic, NOT the 2026-10-08 Thursday frozen bank entry. Never backfill missed windows.

## Acceptance
`SOURCE_ONLY_BANK_GUARDRAIL_PASS` strictly technical; not source profitability, scientific edge, or micro-live. No new results on target strategy.
