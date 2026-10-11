# HYPE-BUYBACK-FLOW-001 — UPLOADED 92-DAY CSV PRIMARY-OVERLAP SOURCE FREEZE V0.4
Freeze date: 2026-10-11 UTC; SOURCE-ONLY, prior to cross-checking official API data against the uploaded CSV. Branch `research/hype-buyback-flow-001-export-reconcile-2026-10-11`. Original 90d requirements remain unchanged.

## Operator-supplied third-party export
File `hyperliquid-trades-2026-07-11-to-2026-10-11.csv.gz` uploaded by user 2026-10-11; raw GZIP SHA256 **eb431a39ed3a826950057a73912bfb2665d25d61e206d854a63ab204dc9b3e4f**; GZIP bytes 3,233,342. Export file itself is NOT copied to GitHub without an operator request.
Source-only read performed locally to build **pre-query expected baselines**, no future price outcomes, strategy rules, return labels, or trade decisions.

### Structural census
- Columns exactly `time,coin,dir,px,sz,ntl,fee,feeToken,closedPnl,hash`.
- 74,159 rows, 92 consecutive calendar dates with >=1 row, first `2026-07-11 00:12:47`, last `2026-10-10 23:43:00`; timezone NOT embedded in CSV, tentatively treat `time` as UTC subject to independent comparison.
- 74,144 spot `@107` Buy rows = 2,188,134.50 HYPE and 166,346,753.87637 USDC executed (px*sz); 15 buys in other markets (@207, @255) strictly excluded from HYPE spot.
- All reported fees, closedPnL blank. 11,121 zero `0x000...0` tx hashes; no `tid` anywhere; no wallet owner, no timestamp milliseconds, no first-available public timestamp. 38 identical full CSV rows; no automatic delete, as they may be valid same-second repeated fills with missing identity.
- This is **large 92-day calendar coverage**, NOT a SOURCE_PASS for full attributed, PIT-executable exact-fill history. Missing `tid`, null hashes and retrospective download prohibit automatic promotion.

### PREDECLARED exact primary-overlap comparison
Use official unauthenticated Hyperliquid `POST https://api.hyperliquid.xyz/info` on EXACT canonical fund address `0x` + `fe`×20, `userFillsByTime`, `aggregateByTime:false`. Three immutable UTC calendar days only:
1. 2026-10-08 00:00:00 to 23:59:59.999 UTC, expected export **1422** source @107 Buy rows, 130 zero hashes; source multiset digest **7c2e7e75b3de52300c8ddf257526dede27990d1cf73176ea0804394b00261853**.
2. 2026-10-09 full UTC day, export **583** source @107 Buy rows, 34 zero hashes; multiset digest **8591df5328050ae5d470e78d16ca309458fee70c5c269af53109ee3db088e744**.
3. 2026-10-10 full UTC day, export **420** source @107 Buy rows, 47 zero hashes; multiset digest **050f9f22edd060a966df34864ea1a034b757f29d50a48db431adfa1eca28d740**.

SOURCE DIGEST CONTRACT (frozen): canonical row key = `(lower_hash, time formatted "%Y-%m-%d %H:%M:%S" UTC, Decimal(px).normalize() as str, Decimal(sz).normalize() as str, coin="@107", dir="Buy")`. For every unique key, record `"|".join(key)+"|"+decimal_occurrence_count`, sort keys lexicographically, join rows with `"\\n"` (real line feed), UTF-8 SHA256; allow duplicate identical rows through multiset occurrence, not set dedupe. The source CSV timestamp is naive, assumed UTC only for this comparison. Filter official fills to exact coin `@107`, side `B` and valid price/size. Require `len(raw_response)<2000`, no HTTP error, no censored endpoints. Store raw official HTTP bodies with SHA256, first-seen UTC, min/max millisecond timestamps, API latency and explicit total vs other-market row counts. If official digest differs, fail closed, inspect only source-shape causes; do not adjust date/time to fit outcome.
Official API `hash` placeholder may be unresolvable; report rather than optimize away mismatches. Do not claim AF export source validated by coincidentally equal gross volumes alone.

Crosscheck script is an independent first-party official feed sampling, with frozen third-party expected multiset hashes for three dates. Official result must pass all three exact keys to establish **RECENT_OVERLAP_MATCH_3D** only. It may NEVER promote the original 90-day gate in isolation.

## Restrictions
No trading, exchange mutations, balance reads, user private data/keys, S3/paid data, wallet interaction, main merge, Render deploy, post-outcome price returns, event-to-price response, 2026 holdout outcomes, or signal tuning. No scheduling/backfill illusion. Preserve all raw and mismatching source receipts for review.
