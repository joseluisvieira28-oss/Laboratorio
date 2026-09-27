# RADAR — BINANCE PUBLIC SOURCE RATE-LIMIT COOLDOWN V0.1 — 2026-09-27

**Status:** FROZEN TECHNICAL SCHEDULER HARDENING / NO SCIENCE CHANGE  
**Authority ID:** `RADAR-BINANCE-PUBLIC-SOURCE-RATE-LIMIT-COOLDOWN-V0.1`

## Observed blocker

Canonical Render runtime on 2026-09-27 returned repeated Binance public-source HTTP 418 responses for:
- `EMA6H-50X200-REGIME-DEPENDENCY-001`
- `OPTIONS-SPOTPERP-001-V2.1`

Both currently use the Binance Spot public market-data family and `/api/v3/klines`.

The canonical scheduler retries a failed EMA6H due boundary or failed OPTIONS runtime day every normal runtime cycle because their success markers are not advanced on exception. With a 30-second runtime loop this creates a retry storm against an already rate-limited source.

Binance documentation classifies HTTP 418 / error -1003 as IP-ban / excessive request behavior and advises avoiding continued polling.

## Frozen remediation

For Binance public-source errors whose exception text contains HTTP 418 or HTTP 429:

1. classify the watcher state as `WAITING_SOURCE_RATE_LIMIT`, never as scientific failure;
2. do not persist a signal, boundary, resolution, missed-event, trade, PnL or rule-deviation event;
3. suppress further calls for **60 minutes**;
4. preserve the original due boundary/runtime day as pending;
5. after cooldown expiry, invoke the same frozen watcher again;
6. if the source succeeds, the watcher catches up deterministically using its already-frozen chronology;
7. if it returns 418/429 again, start a new 60-minute cooldown;
8. non-rate-limit exceptions remain ordinary `FAIL_CLOSED` errors;
9. no alternate market, asset, candle semantics or historical outcome source is introduced by V0.1.

## Scientific invariants

Unchanged for EMA6H:
- universe;
- 15m source bars;
- 6h aggregation;
- EMA 50/200;
- regime definition;
- first eligible boundary;
- hold;
- costs;
- signal/direction.

Unchanged for OPTIONS V2.1:
- CALL_IV_MINUS_PUT_IV signal;
- direction;
- BTCUSDT spot execution identity;
- daily RV20 state;
- weight;
- BASE10 / STRESS20;
- first-50 forward gate;
- execution-shadow gate.

## Health semantics

`WAITING_SOURCE_RATE_LIMIT` is an explicit operational source wait analogous to `WAITING_SOURCE_ARCHIVE`. It is not added to the global scientific/runtime error map while the evidence chain and all other runtime safety checks remain clean.

The state must expose:
- source = BINANCE_PUBLIC;
- HTTP class = 418_OR_429;
- retry_not_before_utc;
- cooldown_seconds = 3600;
- evidence_advanced = false.

## Safety

- public/read-only source only;
- no authenticated exchange API;
- no orders;
- no exchange mutation;
- no wallet;
- no live capital;
- no main merge;
- no rule change;
- no outcome selection;
- no backfill rescue;
- no automatic promotion.
