# EVENT-10M MU V0.2.2 — SOURCE HASH ADJUSTMENT BEFORE ANY OUTCOME

Recorded October 29 2026. Initial historical pilot run #40905998844 failed closed at Yahoo RAW_SHA mismatch and BEFORE any index outcome, feature direction or payout simulation. The earlier V0.2 freeze remains preserved and the failure cannot be reclassified as success. A second pre-outcome source-only canonicalizer run #40906251352 independently re-requested BOTH sources twice and established the actual 1m exchange time + price series were identical, although the Yahoo overall response JSON (dynamic metadata) changed even between consecutive requests.

Validated canonical digests from source-only run #40906251352 (the exact sorted minute epoch seconds + price float pairs, SHA256):
- Yahoo MU CLOSE: aea2418b3308cec57eb1480fcf847ab9e4b82f2f9091b72a8eb14770dfcb6c5d
- MEXC MUSTOCK INDEX OPEN 2026-10-26: a950a8fef646d3773cd415e13a10c55d2e35cbef608bcfa1b02752aa149c884a
- MEXC MUSTOCK INDEX OPEN 2026-10-27: a93f2e96071080ff7769aea2665353a28509623a099928181b4af2341b1c00a3

Both days had 60/60 shared source minute timestamps from 09:30 to 10:30 America/New_York. V0.2.2 modifies ONLY the source integrity comparison from full raw Yahoo payload SHA (unstable metadata) to validated canonical exchange minute/price SHA; the fixed scientific study's symbols, feature age, decision times, 10-minute target, disagreement gating, benchmarks, no-tuning rules and payout sensitivity remain unchanged. All economic outcomes still CLOSED as of this commit.

The run that follows may evaluate its two previously exposed historical days, but any result has no independent edge claim, no authenticated Event Futures payout, no official Nasdaq collector as-of feed, no order execution, and n <= 10. No NVIDIA, SPCX, MLI alias, September 2026 holdout, orders, accounts or main merge.
