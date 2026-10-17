# CRYPTO LAB — CONVEX DIAMOND V02 — PRE-SOURCE & STOP INVARIANTS FREEZE
17 October 2026 UTC; science-only. This freeze precedes all new OKX HTTP probes and any prospective stop-design synthetic test readout. Prior 2023–25 CONVEX model outcomes are already observed; no untouched economic OOS credit can arise here.

## Primary economic blocker: actual venue execution source

Official OKX public historical market data endpoint `GET https://www.okx.com/api/v5/public/market-data-history` documented since September 2025, supports `module=4` 400-level order book, `module=3` historical funding (source: https://www.okx.com/docs-v5/log_en/ ; official endpoint docs https://www.okx.com/docs-v5/en/ ; official GitHub Python SDK https://github.com/okxapi/python-okx/blob/master/okx/PublicData.py). This differs from `/api/v5/market/books` (CURRENT, not historical). Exact current vendor documentation may impose further restrictions; source gate must report literal API code rather than treating HTTP 200 as usable.

Frozen exact public GET matrix, **six requests maximum**, zero retries:
- Four L2 module 4 (400-level), instType SWAP, instFamilyList `SOL-USDT` / `BNB-USDT`, dateAggrType daily, begin=end each of UTC `2023-12-03` and `2024-06-03`.
- Two funding module 3, instType SWAP, instFamilyList `SOL-USDT` / `BNB-USDT`, dateAggrType monthly, begin=end UTC `2024-06-01`.
- Use Unix milliseconds for begin/end, exactly same date per query; maximum 1MB raw response per request and 8s timeout; do not follow returned historical file links; do not download gigabyte books; no private API, wallet, account, account fee request or orders.
- Preserve `HTTP`, `api_code`, `data_item_count`, response_sha256, JSON schema/top-level keys, date/symbol/module, and returned file-link hostnames only if HTTPS and plausibly source-managed; never log full URLs, auth tokens or market prices. If data list includes direct prices or large rows, only output count/schema. Do not infer L2 complete coverage, executable fills or funding semantics from a file link.
- A candidate link must later pass source origin/hash, license, date, pagination, full bid+ask, timestamp, contract specs, venue funding semantics and quote-to-binance-signal alignment. A missing link or error -> SOURCE_BLOCKED. The entire matrix can be SOURCE FEASIBLE but NEVER profitable edge or order proof.
- No external unverified source replacements if blocked; subsequent source family requires new freeze.

## Stop proof: distinguish mechanical risk from economic strategy

Original V5: 4% LONG initial stop, activation after strategy TF completed close >=+5%, conditional 12%-from-peak nonlatched trail; occasionally LOOSENS, per PR #213 BTC closeout. History +59.39% SOL1H etc applies ONLY to original rule. The new **prospective distinct** safety candidate changes its stop policy to MONOTONIC LONG, and MUST NOT inherit historical return performance. Synthetic invariants only:

1. LONG stop can tighten or hold but NEVER lower (with tick rounding conservative toward lower / farther distance when needed). Reject missing previous ACK, inconsistent position ID, direction, stop quantity, tick, nonfinite values, already-crossed bid, too-high risk, stale source, wrong reference.
2. Every pending stop modification is an INTENT only; old acknowledged stop stays authoritative until matched broker-native ACK and subsequent active-stop readback. Unacknowledged write, ambiguous timeout, competing stop, changed position or restart -> FAIL_CLOSED, no blind resend, no false success.
3. Synthetic risks include 0, 1 and 2 ticks, price gaps, stale quotes, lost ACK, duplicate callback and broker quantity mismatch; failures must be reported and never counted as protective stop proof.
4. Never claim gap-loss capped or liquidation impossible. Broker/order transport implementation is OUT OF SCOPE, so broker-ACK cannot be proven by mock.
5. Avoid post-outcome parameter tuning, no cost/fill assumptions changed. Stop safety PASS != historical economic PASS.

## Scientific stop gates

No LIVE GO regardless of CI. For promotion, independently prefreeze one prospective child stop policy and run a full signal-preserving 2023–25 descriptive replay (zero new OOS credit), then untouched 2026 OOS per existing governance, and finally a broker sandbox/venue acknowledgement + reconciliation experiment under separate explicit authorization. Do not rewrite the original V5 record. No main merge, Render, Windows watcher replacement, funds, real orders or leverage.

**Pre-run verdict:** SOURCES_UNVERIFIED / STOP_PROTECTION_SYNTHETIC_ONLY / LIVE_GO = FALSE.
