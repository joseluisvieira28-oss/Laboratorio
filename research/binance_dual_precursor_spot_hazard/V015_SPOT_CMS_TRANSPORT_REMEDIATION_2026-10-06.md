# DUAL PRECURSOR V0.1.5 — SPOT CMS TRANSPORT REMEDIATION
Date: 2026-10-06
Status: PRE-OUTCOME REMEDIATION

Runs 37416824551 and 37416833545 stopped SOURCE_BLOCKED because 198 CMS article-detail requests failed. No predictive rates were computed and 2026 remained closed.

Frozen remediation:
- preserve all existing DUAL, control, horizon and gate definitions;
- prefilter CMS metadata to the already-frozen 2025 Alpha identities before requesting article detail;
- token relevance requires exact ticker evidence in the article title;
- for 1-2 character tickers require parenthetical ticker or an explicit ticker+USDT form;
- fetch only token-relevant article details;
- apply the already-frozen Spot-listing body rule unchanged;
- after deterministic retries, any token with an unresolved relevant article becomes SOURCE_INCOMPLETE and is excluded from both DUAL and control cohorts;
- never interpret a missing article as no Spot listing;
- report HTTP status codes and excluded symbols;
- if the complete-source DUAL primary sample falls below 12, close SOURCE_BLOCKED.

No title-only outcome classification. No 2026 outcomes. No market returns. No post-outcome tuning.
