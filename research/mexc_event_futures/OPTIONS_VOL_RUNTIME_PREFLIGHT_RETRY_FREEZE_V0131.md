# OPTIONS-VOL-FWD-001 — RUNTIME PREFLIGHT RETRY CORRECTION V0.13.1

Date: 2026-10-03
Status: TECHNICAL / PRE-OUTCOME / NO SCIENTIFIC RULE CHANGE

## Trigger

Continuation run 37100149611 ended `FROZEN_RUNTIME_BLOCKED` with:

`ValueError: INDEX_TICK_TIMEOUT`

No source round ran, no shadow observation opened, resolved N remained 0 and statistics were not run.

Evidence shows the MEXC public index stream itself was healthy. The exact payout response was received at local timestamp 1791005620873 ms. ETH emitted valid post-payout index ticks inside the frozen five-second join window, but BTC had no price-change push after the payout response before the five-second timeout. Its last observed BTC push was earlier.

The public `push.index.price` channel is change-driven; a quiet price interval can therefore fail one arbitrary preflight instant without demonstrating a broken source.

## Correction

The frozen event rule is NOT relaxed.

For a real shadow event, the exact rule remains:

- capture a new payout response after the condition receipt;
- use the first valid index push at/after the payout response;
- local payout/index join <= 5000 ms;
- if no such tick exists, that event is BLOCKED.

Only the source/runtime preflight is changed.

Preflight may make up to 12 independent attempts per symbol. Each attempt:

1. obtains a NEW passive browser-generated exact product response;
2. waits at most five seconds for a valid public index push for that symbol at/after that response;
3. records PASS only if the same unchanged <=5000 ms join gate passes;
4. otherwise records the failed attempt and waits at least two seconds before a new attempt.

BTC and ETH may pass on different fresh payout responses. Preflight opens zero research outcomes and evaluates no options signal.

If either symbol fails all 12 attempts, runtime remains `FROZEN_RUNTIME_BLOCKED`.

## Scientific invariance

Unchanged:

- rule hash `edd02c530398465cb35e481f96e336ebd0dcccc73235aaffe6c1d984c3986517`;
- 5 percentage-point skew threshold;
- FOLLOW_INSURANCE_SKEW;
- 10-minute horizon;
- source freshness;
- overlap;
- N=100 per symbol;
- actual payout per event;
- five-second payout/index event join;
- exact expiry rule;
- 30-day frozen evaluation boundary.

This correction cannot turn any failed or missed signal into an observation after the fact.
