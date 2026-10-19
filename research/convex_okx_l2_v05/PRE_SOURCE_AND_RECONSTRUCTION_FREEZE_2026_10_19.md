# CONVEX V05 — OKX HISTORICAL 400-LEVEL BOOK SOURCE FREEZE — 19 OCT 2026

**Source/read-only research.** This freeze is committed BEFORE new V05 public responses. V04 was in-sample descriptive only: SOL 1h 32/33 fresh Binance Futures L1 quotes with full-size capacity 15/32; BNB 4h 6/6 fresh with full-size capacity 3/6; even a 0.25x SOL position cannot satisfy 90% one-level size gate. These are source observations, not executed fills or independent alpha.

## Precise question

Is there authenticated **OKX SWAP 400-level historical order-book data** for two precommitted **original Binance V5 signal-entry UTC instants**, such that a chronological ASK-sweep on OKX could eventually be constructed, with custody, historical contract multipliers, gaps and real costs? The presence of a public catalogue is not proof of an L2 archive or a fill.

## Frozen two historical venue/source dates, no outcome selection

- SOL-USDT-SWAP / `instFamilyList=SOL-USDT`, original SOL1h LONG 2023-05-29 16:05:00.000 UTC; source catalogue UTC day 2023-05-29
- BNB-USDT-SWAP / `instFamilyList=BNB-USDT`, original BNB4h LONG 2023-11-01 16:05:00.000 UTC; source catalogue UTC day 2023-11-01
- These are the earliest previously accepted fresh source quotes from frozen source experiment V03. NOT chosen on PnL or OKX quote results; 2026 holdout untouched. Venue-specific instrument must have existed at selected time; historical contract `ctVal,ctValCcy,lotSz,minSz,tickSz` MUST be verified separately. Never treat Binance base-asset qty as OKX contract qty.

**Exactly TWO anonymous public GETs**, no retries/automatic branch push repeats:
`https://www.okx.com/api/v5/public/market-data-history?module=4&instType=SWAP&instFamilyList=SOL-USDT&dateAggrType=daily&begin=1685318400000&end=1685318400000`
`https://www.okx.com/api/v5/public/market-data-history?module=4&instType=SWAP&instFamilyList=BNB-USDT&dateAggrType=daily&begin=1698796800000&end=1698796800000`
Response HTTP/status/sha, date/module, source item count and nested field shapes only. Never emit entire file URL, query token, API secrets or raw prices. MAX 1MB response, timeout 10s, no redirects off original hostname. No headers containing auth. If HTTP403/429/451 or unexpected schema -> SOURCE_BLOCKED, no bypass, no new dates or domains.
- Determine whether `groupDetails` or nested fields include a **recognizable public HTTPS archive URL and original UTC file day/instrument**. Log only URL hostname and SHA256 of stripped/sanitized path (no query), not the download link. Avoid following URL in V05; no purchases, no 500MB files without separate file provenance/terms gate.
- Do not relabel a nonempty catalogue response `RAW_L2_VERIFIED`. Only `CATALOGUE_LINK_CANDIDATE` where an actual approved publisher archive link for exact date/instrument is identified; otherwise `CATALOGUE_SCHEMA_ONLY` or `SOURCE_BLOCKED`.
- Official OKX page https://www.okx.com/historical-data claims high-resolution L2 since March 2023; OKX Sept 2025 API publication supports module 4 for 400 levels and 2026-08-06 limit tightened to 10 days; two one-day windows comply. The live `/api/v5/market/books` is NOW and NEVER a substitute for historical L2.

## Offline L2 engine predeclared independently from unavailable market outcomes

For one **verified** historical OKX `SOL-USDT-SWAP` or `BNB-USDT-SWAP` stream:
- Require exact instrument, contract multiplier and unit, UTC event timestamp, initial full snapshot, changes in chronological sequence, valid bid<ask, positive integer/decimal quantities, and no missing `prevSeqId/seqId` chain when present. Reject any gap, crossed book or source timestamp > original signal. Verify publisher origin/hash and period before admitting live historical files. Ignore extra price levels beyond original genuine 400 but never invent missing levels.
- For LONG original entry, take latest admissible historical prior-state `<= T0` only and max quote age 2s; convert the original hypothetical BASE order's **base-asset** qty into **contracts via historically verified ctVal** only when the instrument is linear and quote is USDT. Sweep ASK prices ascending, consume contracts to target, output theoretical ASK VWAP, walking cost versus first ASK in bps, remaining unfilled contracts, and coverage flag. NEVER use original Binance fill as a factor to estimate OKX depth.
- Mirror for exit on BID only after verifying a valid EXIT timestamp/source and frozen stop trigger; stops can jump/gap. No broker-native order ACK, no actual fill or exchange execution is ever implied.
- Do NOT infer maker queue/fill, liquidity renewal, fees, funding and tax/account-specific rates from L2 alone.
- Local/synthetic test cases cover 1-level full, multi-level full, partial book, crossed book, missing snapshot, source future, source stale, sequence hole, qty contract multiplier, best-price price impact, and book update deletion.
- No parameter fitting on market outcomes, no historical 2026 protected holdout; old V5 original 2023–25 outcomes stay immutable. Even two perfect source confirmations **cannot certify profitable trading**.

## Legal and operational guardrails

Only public source metadata. Historical files can have license or geographic constraints. **Do not assume account eligibility in Switzerland, download file or request authenticated access** from user's statement. If manual user download/license is required, ask for exact archive files or a user-approved read-only source; never request private keys, passwords, trading permissions or wallets. No change main, Render, Windows Telegram, orders or crypto assets.

Outcome status is `SOURCE_METADATA_UNVERIFIED` until the actual GET receipts are observed. All outputs NO LIVE GO, no independent edge, no order authority.
