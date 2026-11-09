# Execution evidence and collection gate â€” 2026-11-05

**NO-GO collection; LIVE NO-GO. Forward V3 0/20.**

## Executed verification

Python 3.12.14, isolated local venv `.v3-offline` without pip or installed
dependencies. Initial standard venv creation failed at ensurepip; the pip-free
environment succeeded. No package download. Ran:

```
.v3-offline/Scripts/python.exe research/deribit_v3_microstructure/run_checks.py
```

55 tests PASS, zero failures/errors: V2 30, Economic Proof Engine V1 14,
V3 11 (3 existing comparator + 8 adapter). Outbound socket connect/connect_ex
and create_connection denied. The transport unit test uses a mocked HTTP
response, not a market observation. See `test-results.txt` and
`verification/receipt.json` for source SHA256, Python version and parent SHA.
Receipt hashes identify the tested working sources; parent SHA alone does not.
Legacy synthetic settlement stdout is fixture output, not validated BTC_USDC
daily cash flow or prospective profit. Passing legacy fee tests only reproduces
frozen code; it does not certify the weekday fee assumption.

Historical replay: three pinned archives, 18 original raw-response hashes,
two technically valid historical rejections, zero V2 gate passes. Adapter also
decodes all six archived books, matches original raw hashes, and independently
rejects 3 November on synchronization. Original archives remain untouched.
Historical friction remains 13.959579% / 17.599301%; net PnL remains null.

## Adapter audit

New `adapter.py` exposes a single bounded public GET for order books. Product
identifier allowlist, fixed HTTPS host/path, no redirects, no authentication,
15-second timeout, <=12MB decode limit, no retry. Raw bytes are returned intact
with SHA256, request/receipt time, source book timestamp, age, full returned
depth, bid/ask and source provenance. Closed/crossed/empty/duplicate/unsorted
books, insufficient best-level depth, invalid numbers, stale/future quotes,
wrong product or environment fail closed. Each book is compared with index
receipt time, with <=1000ms leg skew and <=10s per-book distance. No PnL formula.

Static V2 findings in COLLECTOR_READINESS_AUDIT remain applicable: index
distance uses newest book only and delivery uses weekday heuristic. Neither
was changed. Diff against parent #340 contains no V2/Economic Engine changes.

This is a tested book adapter, not a certified session collector. Remaining
integration gates: independent product metadata/expiry/ATM selection validation,
source-and-decision window checks, concurrent pair dispatch and immutable
on-disk raw/manifest/session-ledger persistence with failed attempts retained.
Returned bytes must be persisted before decoding failures are discarded by any
future session wrapper. A fixture pass does not establish live transport quality.

## Fees rechecked on 5 November

Official [Fees](https://support.deribit.com/hc/en-us/articles/25944746248989-Fees),
page marked updated 5 November 2026 09:16, delivery section simultaneously
exempts daily options and lists BTC/ETH daily at 0%, while USDC linear options
are listed at 0.015% capped at 12.5% of option value. Product-specific precedence
for **BTC_USDC daily** is not explicit. The
[linear guide](https://support.deribit.com/hc/en-us/articles/31424932728093-Linear-USDC-Options)
describes conversion through an expiring future; it does not remove the category
ambiguity. **UNVERIFIED / BLOCKER for expiry economics; net_pnl=null.** No
support message sent and no zero-fee weekday inference adopted.

Forced liquidation is a separate event: the USDC option table gives total fee
min(0.19% * index, 25% * option price) * contracts * contract size, including
regular trading fees. It must not be added as an extra full charge on top of
normal trading fees or confused with expiry delivery. Daily mark-to-market
settlement has no fee per the official
[settlement guide](https://support.deribit.com/hc/en-us/articles/29734325712413-Settlement).
Neither statement resolves BTC_USDC daily expiry delivery classification.

## Prepared 20-session start checklist

Follow PRE_REGISTRATION without changing thresholds or V2. Before start:
complete the session integration gates above and test invalid attempt retention;
perform one explicitly labelled controlled public observation, save exact raw
bytes/manifest and independently verify hashes/timing; freeze the collector
version and precommit hash before the first session. The diagnostic is not one
of the 20. Retain all attempts; select one deterministic snapshot within
08:05â€“08:10 UTC, next-day expiry, .01 per leg, depth >=.05, ATM <=1%, skew <=1s.
Keep historical, fixtures, diagnostics and prospective evidence in distinct
namespaces. Stop at 20 valid sessions, retaining invalid attempts separately.
Unresolved delivery terms block economic conclusions, even if quote collection
is subsequently cleared. A collection GO can never authorize LIVE.

No collector was activated; no workflows, schedules, orders, exchange
credentials, paid resources, main changes or merges. New scheduling/workflows
require additional approval. Current collection NO-GO also reflects absence of
the controlled observation and complete session wrapper, independently of fees.
