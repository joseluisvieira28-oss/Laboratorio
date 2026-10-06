# CEX-MARGIN-COLLATERAL-FORCED-DELEVERAGING-001 — V0.1 CLOSEOUT
Date: 2026-10-06
Verdict: **SOURCE_BLOCKED**
Historical mechanism hypothesis: **NOT TESTED**
Discovery activation: **DENIED**

## Authority / chronology
Operator mission and V0.1 SOURCE/MECHANISM FREEZE were committed before this mission's census or any market outcome: freeze `605bcf8ff16d9ac493b6ff175778866a4420715b`.
Source runner committed as `ebbd6af5ba091b62f20f0e0eca12c81017bfe10d`; source census/provenance checkpoint `2e3ba41c020ecc6cef0f98c24664970b1f40d6b0`.
Local execution ID: CEXMCD-SOURCE-20261006T072318Z. The UTC timestamp identifies the persisted census receipt. No GitHub Actions run was launched; do not invent a run ID.

## Exact source numbers
- Binance public CMS catalogs: 48, 49, 161, 157.
- Pages scanned: 19 + 27 + 6 + 8 = **60**; each reached below 2024-01-01. Zero final catalog transport failures.
- Unique catalog articles published in 2024–2025: **2,114**.
- Outcome-independent title candidates: **198** = **121** published in 2025 + **77** in 2024.
- Details attempted: **198**; recovered: **84**; unavailable after two attempts: **114**, all final failures HTTP **429 Too Many Requests**.
- Article-detail transport coverage: **84/198 = 42.424242%**. This is NOT event-window market coverage.
- Diagnostic source tags (overlapping; not event counts): **37** recovered bodies mention existing positions affected; **12** declare an amendment/revision; **21** contain automatic-settlement language requiring confound/binding review.
- Historical pre-effective provenance accepted: **0**.
- Independent event clusters accepted under the frozen full gate: **0**. This is not evidence that zero eligible events exist.
- Bounded archive diagnostics: **15** CDX requests across the recorded probes; **4** returned empty results and **11** failed by transport. Earliest-12 diagnostic alone: 3 empty / 9 transport failures. No accepted capture. Exact URL/path/time filters are in receipts; alternative paths and unqueried notices remain unexhausted.
- Outcomes opened: **0**. Development runs: **0**. 2026 outcomes: **CLOSED**.

## Why this is SOURCE_BLOCKED
1. **Historical content provenance is not established.** Current public pages contain real policy changes, but publication metadata alone does not prove that today's rules/deadlines were the content available before implementation. CMS `version=1` and `lastUpdateTime=0` are insufficient: the September-2025 example reports a revision in its body despite both values. Current hashes preserve what was retrieved today, not a pre-effective version.
2. **Detail retrieval is incomplete.** 114 final HTTP 429 failures are a recoverable transport limitation, not missing-event zeros, absent notices, or an economic failure. They were not silently excluded to create a favorable universe. The runner's immediate two-attempt retry is not sufficient for a rate-limited historical crawl; further source work would need a cooldown/paced cached collector, rather than another concurrent replay. Even recovering these current bodies would not itself repair historical provenance.
3. **The mechanism cannot be inferred from a headline.** Existing-position exclusions, relaxation vs tightening, collateral substitution, conditional liquidation, and settlement confounds need individual adjudication. Reducing collateral on token X does not identify which contracts borrowers financed. Same-venue historical OI must be bound to actual affected derivative exposure, not selected by a matching ticker.
4. **Venue expansion did not supply an accepted alternative universe.** Bybit operative body/image recovery failed; the current help page is revised in 2026 and describes gradual 2025 rollout. OKX has old/new tier notices, but sampled implementation intervals are 06:00–10:00 UTC and policies can be postponed; no exact per-contract deadline plus immutable pre-effective content and complete same-venue OI/basis/funding coverage was established. These are bounded source diagnostics, not an exhaustive venue census.

## Market source capability — strictly limited claim
HEAD-only requests returned HTTP 200 for ACTUSDT April 1, 2025 metrics/OI, mark and index archives, plus April-2025 funding archive: **4/4**.
No ZIP body or numeric market value was read. No checksum/content/schema/event-control-window verification was performed on these four archives. This demonstrates sample object accessibility only; it is not SOURCE PASS or >=80% event coverage. No event-market coverage denominator exists because no event universe was accepted.

## Decision and prohibited inference
The >=12 independent defensible-observation requirement was not met with accepted source evidence. **Do not label INSUFFICIENT_SAMPLE**, because a sufficiently complete accepted historical universe has not been established. **Do not label NO_EDGE_DISCOVERY**, because no economic test occurred. No PRE-OUTCOME ANALYSIS FREEZE was activated; no development, execution, holdout or forward event was activated.

This closes the V0.1 historical source attempt. It does not prove that mandatory collateral/risk changes lack market effects. No survivor/diamond or trading authority exists.

## Reopening requirements — source only
Recover historical official content demonstrably available before the corrected exact deadline; resolve amendment chronology; establish compulsory effect on existing exposure and quantified tightening; bind same-venue OI/basis/funding archives to affected exposure. Build the full universe without outcome selection and meet the frozen >=12 independent covered clusters and >=80% event coverage. A new source receipt can supersede the blocker only with new evidence. A separate pre-outcome analysis freeze is still mandatory before any numeric outcome.
No forward-only research authority or scheduled watcher was created in this mission.

## Evidence / validation
`SOURCE_CATALOG_RECEIPT.json.gz` preserves the catalog census and request hashes. `SOURCE_NORMALIZED_EVIDENCE.json.gz` preserves recovered official body text, timestamps, CMS metadata, payload hashes and all transport-failure records. These archives are current source evidence, not historical pre-effective snapshots.
`SOURCE_CENSUS_SUMMARY.json`, `SOURCE_DETAIL_SUMMARY.json`, `PROVENANCE_CAPABILITY_RECEIPT.json`, `ARCHIVE_REVISION_RECEIPT.json`, `ARCHIVE_BATCH_RECEIPT.json`, `BYBIT_IMAGE_TRANSPORT_RECEIPT.json`, and cross-venue adjudication document the scope and limits.
Python syntax checks passed; gzip round-trip and catalog SHA256 verified. All writes confined to the research branch/directory. No main edits/merge, live trading, orders, accounts, wallets, private/authenticated exchange endpoints, exchange mutation or post-outcome tuning.
