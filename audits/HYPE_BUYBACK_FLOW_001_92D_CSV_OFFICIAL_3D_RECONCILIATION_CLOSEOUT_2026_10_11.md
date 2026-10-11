# HYPE-BUYBACK-FLOW-001 — 92-DAY USER EXPORT OFFICIAL RECONCILIATION CLOSEOUT V0.4.2
UTC: 2026-10-11
Verdict: **92D CALENDAR SOURCE STRUCTURAL COVERAGE PASS; 3D OFFICIAL SOURCE SEMANTIC MATCH; ORIGINAL ECONOMIC/HISTORICAL POINT-IN-TIME GATE SOURCE_BLOCKED.** This is NOT NO_EDGE, NOT profitable, NOT a source promotion to full historical economic gate. Trading Authority: NONE.

## Authority and audit lineage
Parent authority: `research/hype-buyback-flow-001-source-gate-2026-10-10/research/hype_buyback_flow_001/SOURCE_GATE_AUTHORITY_V0_1.md`. Parent corrected audit: `audits/HYPE_BUYBACK_FLOW_001_SOURCE_ECONOMICS_CORRECTED_VERDICT_V02_2026_10_10.md`.
Free archive source hunt closeout `audits/HYPE_BUYBACK_FLOW_001_FREE_90D_SOURCE_HUNT_CLOSEOUT_V03_2026_10_10.md`. User subsequently supplied actual .csv.gz as requested. V0.4 **fixed three-day primary source overlap** preregistered at commit `e7fab33b945cbf4fcfddef9d62a3bf3cee21a656`, **before** official lookup. All prior strict receipts retained.

## Operator file and structural census (SOURCE ONLY)
- File exactly `hyperliquid-trades-2026-07-11-to-2026-10-11.csv.gz`, 3,233,342 bytes; SHA256 `eb431a39ed3a826950057a73912bfb2665d25d61e206d854a63ab204dc9b3e4f`. **Provided in the chat, not committed as binary to GitHub.**
- 74,159 records from 2026-07-11 00:12:47 to 2026-10-10 23:43:00, 92/92 consecutive active calendar dates. File timestamps are timezone-naive with second precision.
- Spot HYPE/USDC `@107` BUY: **74,144** rows, **2,188,134.50 HYPE**, **166,346,753.87637 USDC** px*sz historical executed **raw** notional (NOT profits, not volume of independent opportunities). Other 15 rows: `@207` 4, `@255` 11.
- Empty `fee` and `closedPnl` on all rows. No arithmetic mismatch >0.00001 USDC. CSV schema: `time,coin,dir,px,sz,ntl,fee,feeToken,closedPnl,hash`; no wallet column, no `tid` and no first-seen ingestion timestamp.
- 11,121 rows have `0x000...000` hash placeholder (**14.996%**). 38 identical full CSV rows, **all 38 occur among zero-hash rows**. Do NOT automatically delete these; duplicate real fills vs export artifacts cannot be proved from CSV alone.
- Around 683 HYPE spot source `sz` cells have binary float render tails (e.g. `7.9399999999999995`) deviating by <= 5e-16 from exact cent lots. The archive is a third-party retrospective export, not a real-time tape with causal visibility proven.

## Original preregistered official fixed-day crosscheck: status and rigorous preservation
Official public `POST https://api.hyperliquid.xyz/info`, `userFillsByTime` for exact 42-char AF system address, UTC full days **2026-10-08 / 09 / 10**, `aggregateByTime:false`, fixed PRIOR csv-count and multiset hashes. GitHub Actions **38121995440**, commit `286533969a154cd153c6fa2b3828c7ef6dfd8d69`. All official responses HTTP200, none reached 2000 cap; artifact **11694999308**, archived ZIP SHA256 `3277d5f7e09271a9aea85436e6219f1dc62cd2f89f665092785af7d1bb7b0968`.
- Day 08/10: CSV 1422 / official 1422 / zero-hash 130 / original frozen *strict* SHA mismatched.
- Day 09/10: CSV 583 / official 583 / zero-hash 34 / original frozen strict SHA mismatched.
- Day 10/10: CSV 420 / official 420 / zero-hash 47 / original frozen strict SHA mismatched.
- Official diagnostic run **38122096850** preserved actual exact source fields, proved first/last UTC seconds, price, size and tx hash visibly aligned with original export. V0.4.1 technical diagnostic freeze commit `4d87fa1fe52a3434ab3f9395d228b9dfc24cfc05`. Scientific original strict digest FAIL remains FAIL; it was NOT silently overwritten.

## Additive offline numerical representation reconciliation — zero outcomes, all raw inputs immutable
After V0.4 strict mismatches, both archived official HTTP *raw* source bytes and the supplied operator GZIP were independently read offline; NO new market outcome queries. A fixed numeric transport representation check was applied ONLY to `sz`: accept `Decimal(sz)` quantized to 2 cents **only where |source sz - 0.01-lot sz| <= 1e-10**. `coin, side, px, hash, UTC-second` left unchanged; preserve multiplicities with multiset, NOT set dedupe.
- 2026-10-08: 1,413 byte-equivalent canonical rows; 9 binary float display mismatches; after safe size representation normalization **1,422/1,422 exact multiset match**. Digest both sides `f66ce8e61d8876914d8b4591cc3461d161b8f9292dc8e0409673bc94d3955b2f`.
- 2026-10-09: 580 strict rows, 3 numeric text mismatches, **583/583 additive semantic source match**. Digest `63ee54f9c3526ac35039ce4e85574bb555e98a23f4f70f59d5644eeb59d7c08c`.
- 2026-10-10: 419 strict rows, 1 numeric text mismatch, **420/420 additive semantic source match**. Digest `6fb92fcec5aa2e51e0fa7c0860b0b75824072d0f4b3a9fd11942dfba76cd2ac6`.
- Total **2,425/2,425** SOURCE records semantically matched, ZERO unpaired records, 13 purely binary float-display disagreements. **All 211 null hashes** in this overlap were ALSO null in official API. Strong non-null transaction-hash multisets agree on all three days. Date UTC and Assistance Fund wallet origin validated for those three *overlap* days, NOT historically generalized to all 92 days.
- Official sample has `tid` for all 2,425 rows; user export has **no `tid`**. Official sample has `crossed=false` in **2,425/2,425** fills and exactly 988 distinct order ids (597+210+181), hence fills are NOT independent buy decisions. Do not infer front-running or passive order economic alpha directly. NULL-hash rows are real source rows in recent overlap, but underidentifiable from third party CSV alone.
- Offline details available in user-provided conversation as generated `HYPE_BUYBACK_OFFICIAL_3DAY_CROSSCHECK_2026-10-11.json`, with per-date raw SHA and normalised semantic digest. No raw user file copied to public repo.

## Source PASS and economic research NOT permitted yet
Original preregistered gate requires >=90 FULL attributable UTC days, >=60 active days, exact individual event IDs without unexplained gaps, historical first-public-observable clock, official independent verifiability, and historical bid/ask+depth to model *actually executable* edge. User CSV satisfies **calendar days / 92 active**, and current 3-day samples are extraordinarily consistent with first-party official receipts; but full archive **does not carry tid, milliseconds, wallet and first-seen**, with 11,121 placeholder hashes and 38 ambiguous duplicate textual rows, and no PIT availability evidence or historical quotes. 90d unique exact-fill source coverage and causal observability **NOT ESTABLISHED**. This remains **SOURCE_BLOCKED_90D_PROVENANCE_PIT**; trading authority NONE. Avoid any post-outcome tuning.

## Next science-only action
Do not spend/trade. Independently design a newly frozen *prospective append-only* public fills/quotes collector with `tid`, `oid`, `time_ms`, first-seen/received timestamps, page/completeness checks, snapshot quotes, duplicate/no-gap logic and durable upload. Do not call a non-main scheduled GitHub Actions workflow "active" by assumption; a real supported external scheduler or explicit deployment authority must be recorded. Only once source/time/quote proofs pass immutable gates, commit a complete economic hypothesis **before** looking at post-event HYPE returns. Earlier source-blocked CSV itself is not an alpha PASS.
