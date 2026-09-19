# CROSS-VENUE-DIAMOND-REPLICATION-002 — OKX STAGE-B EXACT REPLICATION FREEZE — 2026-09-18

Status: FROZEN_AFTER_OKX_FULL_SOURCE_DATA_PASS_AND_MARK_PRICE_SOURCE_PASS_BEFORE_ANY_OKX_OUTCOME_CALCULATION

Candidate: CED1D-0031 — AVAXUSDT Momentum 20D CONTINUATION H1
Venue: OKX AVAX-USDT-SWAP
Parent implementation: exact CED V0.3 hypotheses module

## Immutable parent identity

- V0.3 runner ZIP SHA256: df625d0d4a05c55ba34ca51514d31fd61636ff0a823567585c2d02afa0877958
- hypotheses.py SHA256: dc52cdc16aee0ba586ec7081a39ce68d62c5544e9bd27186255b4d9a87368693
- family: A_MOMENTUM
- symbol adapter only: AVAXUSDT parent identity -> AVAX-USDT-SWAP venue source
- lookback: 20 calendar days
- horizon: 1 day
- direction: CONTINUATION
- BASE nonfunding round-trip cost: 14 bps
- STRESS nonfunding round-trip cost: 20 bps
- parent complete signal weeks: 2025-01-06 inclusive through 2025-12-29 exclusive
- one-active-trade / overlap semantics: exact V0.3 implementation
- no manual reconstruction of signal_for or Series.execution is permitted.

## Frozen source authority

OKX full source gate:
- run: 35364301053
- artifact: 10554478995
- artifact digest: sha256:097e17489be37e366926b03901fc1e124ba4a2a3922f35b7e2fd96c4a1208901
- result: OKX_FULL_SOURCE_DATA_PASS
- 16 byte-hashed monthly 1m trade-candle archives from 2024-09 through 2025-12
- 12 byte-hashed monthly funding-rate archives from 2025-01 through 2025-12
- zero cross-file 1m candle gaps; zero duplicate timestamps.

OKX mark-price source gate:
- run: 35364619561
- fingerprint: d8a90213ee3b653ef480a14c91f7a85830e28b9fe890c77b9d62e3cb48c704d2
- result: OKX_MARK_PRICE_SOURCE_PASS
- public endpoint: /api/v5/market/history-mark-price-candles
- bar: 1m
- exact 2025 anchors at 00:00/08:00/16:00 UTC retrievable.

The Stage-B runner hard-codes every source-gate ZIP SHA256 before opening outcomes and fails closed on any mismatch.

## Venue adapter

1. Re-acquire only the frozen OKX monthly archives and require exact frozen SHA256.
2. Parse 1m trade-price rows and map them into the parent UTC-daily input:
   - UTC date boundary, not OKX UTC+8 archive boundary;
   - daily open = earliest 1m open;
   - daily high = max 1m high;
   - daily low = min 1m low;
   - daily close = latest 1m close;
   - valid day requires exactly 1440 unique minute timestamps and an exact 00:01 UTC open.
3. Import the exact frozen V0.3 ced1d.hypotheses from the byte-verified runner ZIP.
4. Generate events only through hyp.signal_for(...) and Series.execution(...).
5. 2025 only. Any execution exit reaching 2026 is DATA_UNAVAILABLE.
6. Preserve parent overlap blocking exactly.

## Funding

Use actual OKX funding events from the frozen archive.

For each TRADE:
- entry timestamp = parent entry_day 00:01 UTC;
- exit timestamp = parent exit_day 00:01 UTC;
- include funding settlements strictly entry_ts < fundingTime < exit_ts, identical boundary semantics to parent;
- for each settlement T, retrieve the OKX 1m mark-price candle with timestamp exactly T;
- no nearest timestamp, interpolation, trade-price substitution or index-price substitution;
- funding rate comes only from the frozen module-3 archive;
- settlement uncertainty is bounded exactly in parent style:
  - coeff = -direction * funding_rate / entry_price
  - settlement contribution endpoints = coeff * mark_low * 10000 and coeff * mark_high * 10000
  - lower adds min(endpoint pair); upper adds max(endpoint pair).
- if exact mark candle T is absent or unconfirmed, that event is execution/source unresolved and cannot be silently removed.

## Reporting paths

Conservative adjudication path = LOWER funding bound.

Per-path report:
- inference N;
- BASE mean bps/event;
- BASE PF;
- STRESS mean bps/event;
- positive active months / total active months;
- positive quarters;
- leave-one-month-out all positive;
- month/day/top-5 concentration diagnostics;
- UTC-week block-bootstrap 95% interval, 9999 reps, seed 20260908.

## Frozen label rule

First evaluate LOWER path.

CROSS_VENUE_FAIL if any:
- BASE mean <= 0;
- BASE PF <= 1;
- STRESS mean <= 0;
- fewer than half active months positive;
- any source/execution unresolved TRADE;
- source hash/rule deviation.

If all hard economics survive:
- CROSS_VENUE_SURVIVES only if bootstrap lower 95% > 0, at least 2/3 active months positive, >=3 positive quarters, leave-one-month-out all positive, and parent-style concentration ratio <=1.
- otherwise CROSS_VENUE_FRAGILE_SURVIVAL.

UPPER path is diagnostic only and can never rescue a LOWER-path failure.

## Governance

- Binance parent verdict immutable.
- Bybit remains SOURCE_BLOCKED_ENVIRONMENT unless separately remediated; it is not dropped or relabelled economic failure.
- no 2026+ access;
- no post-outcome tuning;
- no cost reduction;
- no direction flip;
- no calendar subperiod selection;
- no event deletion;
- no venue dropping;
- no live trading;
- no authenticated exchange API;
- no orders;
- no wallets;
- no exchange mutation;
- no alerts/webhooks;
- no merge to main.