# DIAMANTE V9 — BNB Launchpool incremental source authority — 2026-11-16

## Scope and immutable parent
Research-only, source-only, incremental follow-up to PR #348 (V8). Does not replace or retune the frozen BNB-LAUNCHPOOL-DEMAND-001 trading protocol or its Diamond V0.2 25-event test.
V8 has evidence of complete catalogue 48 pagination (40 pages; 1,922 distinct codes), and cross-category catalogue 49/93/128 requests were rate-limited HTTP 429. No market outcome or new qualifying prospective trade was evidenced.

## V9 pre-source test freeze
- Branch: `research/bnb-launchpool-source-v09-incremental-2026-11-16`.
- Parent V8 branch base SHA: `3c757e0117147ad3b43c95b118827a35b52fdc51`.
- Selected official Binance public CMS GET-only path: `/bapi/composite/v1/public/cms/article/catalog/list/query`, catalogue 49 for first bounded execution; 93 and 128 remain unverified, research-only categories.
- Strict maximum **one HTTP GET per invocation**, no retry on HTTP 429, no proxy/fallback/rotating IP/scraping bypass; no POST, authentication or market prices.
- Enforce a global >=1-hour 429 cooldown, plus the provider-specified Retry-After if longer. Enforce >=15 min gap per category in the checkpoint. If the server rejects or throttles, stop and preserve the checkpoint unchanged at that page.
- SHA-256 chain: raw response SHA per page, digest-protected JSON checkpoint, separate immutable GitHub Actions artifact per execution; GitHub Actions cache is an operational resume mechanism, **not a permanent historical authority**.
- First-seen timestamp is the earliest **V9 observation** from an actual successful request. Article publication time is not first-seen time. Historical announcements first discovered today are not retrospectively eligible Diamond events.
- PAGE_SIZE=50; page cursor and deduplication; reject invalid Launchpool article codes, repeated pages, unexpected JSON shape and empty initial pages; never report zero eligible events from a partial/blocked listing.
- No detail API requests or trade eligibility decisions in this initial rate-limit probe; Launchpool titles are *unverified candidates*, not qualifying BNB Launchpool triggers.
- Because pages can move as new articles appear, a multi-run crawl is not an atomic historical snapshot; even all pages scanned is not automatically a proof of a complete, contamination-free forward sample.
- Explicit scientific decision states: `INCREMENTAL_PAGE_OBSERVED__NOT_FORWARD_PROOF`, `HTTP_429_SOURCE_BLOCKED`, `SOURCE_ERROR_BLOCKED`, `SCHEMA_ERROR_SOURCE_BLOCKED`, `CATALOG_PAGINATION_REACHED_END__NOT_FORWARD_PROOF`. No Tier 1 or GO live comes from any of these.

## Acceptance gates
1. Offline fail-closed regression tests pass: 429, Retry-After integer/date, no retry, global cooldown, missing state, hash tampering, page duplication/schema, first-seen immutability/no backfill.
2. Exactly one real category-49 request is attempted when the frozen V9 run executes. Save its outcome, including failure, to an immutable artifact.
3. No market outcomes, no replay of missed entry time, no accepted forward trades, and no relaxed threshold.
4. This run's terminal verdict reports the observed *source status* and explicitly holds the inherited V3 Tier 2 / Diamond test scientific status.

## Forbidden
Orders, account API calls, wallets, trades, market-price/PnL reads, retrospective source-to-trade reconstruction, signal activation, GitHub merge into main or Radar, Render deploy, Telegram alerts, brute-force retries, or bypassing Binance 429 limits.

## Decision philosophy
Do not confuse a green CI test with an economically proven edge. If Binance sends 429, V9 is `SOURCE_BLOCKED`; this is a measured operational limitation and not a market NO_EDGE verdict. The next legal source request may occur only after the server's cooldown and with the approved request budget.
