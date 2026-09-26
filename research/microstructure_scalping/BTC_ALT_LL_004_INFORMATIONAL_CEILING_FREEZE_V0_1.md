# BTC-ALT-LL-004 — MICRO LEAD-LAG INFORMATIONAL CEILING
## FRESH DISCOVERY PRE-RUN FREEZE V0.1

Date: 2026-09-26
Status: PRE-OUTCOME FREEZE
Phase: DISCOVERY ONLY

## Hypothesis
A sufficiently large, observable BTC micro-shock may lead a delayed same-direction move in ETHUSDT or SOLUSDT over the next seconds/minutes.

This is distinct from H180-0001:
- H180-0001 = hourly lead-lag.
- BTC-ALT-LL-004 = 1s/5s shock with 1s–120s follower response.
- No H180 thresholds or outcomes are reused.

## Fresh Discovery dates
Calendar rule frozen before outcomes:
first Wednesday of the next three months after SWEEP-003's final date.

- 2024-05-01
- 2024-06-05
- 2024-07-03

All are inside the existing 2023–2024 Discovery partition.
2025 OOS = LOCKED.
2026 protected holdout = LOCKED.

## Efficient ceiling design
This first MVE is deliberately an optimistic INFORMATIONAL upper bound.

Downloaded:
- BTCUSDT L2, first 250,000 messages
- BTCUSDT historical trades
- ETHUSDT historical trades
- SOLUSDT historical trades

Follower L2 is NOT downloaded in this ceiling.

Follower entry/future prices use public trade prices, therefore:
- no spread
- no slippage
- no queue cost
- no adverse selection

Only the current MEXC fee hurdle is subtracted.

If this optimistic ceiling cannot clear fees, executable follower-L2 simulation cannot rescue it.

If a survivor exists, the next gate MUST download follower L2 and retest executable BBO economics.

## Source fail-closed
Before any outcome computation, every required URL for all three dates must return HTTP 200 with positive Content-Length.
Any missing source blocks the run.

## BTC event clock and anchors
- BTC L2 event clock = cts when present, otherwise ts
- 1-second anchors
- shock windows: 1s and 5s
- BTC prior mid return is computed using only states at/before anchor
- BTC aggressive flow uses only trades timestamped strictly before the anchor

## BTC shock calibration
Use 2024-05-01 only to derive feature thresholds from abs(BTC prior return).

For each window:
- p95
- p99

No follower outcome is used to create thresholds.

## Flow confirmation
Trailing BTC aggressive flow window equals the shock window.

signed_flow = (buy_notional-sell_notional)/(buy_notional+sell_notional)

Agreement:
sign(signed_flow) == sign(BTC shock)

No flow-magnitude tuning.

## Follower lag condition
At anchor t, follower prior return over the same 1s or 5s window is computed from last historical trade at/before each boundary.

Require quote/trade staleness <= 250 ms at each boundary.

Underreaction condition:
direction(BTC) * follower_prior_return_bps < abs(BTC_prior_return_bps)

This is a causal condition; it does not use any future follower move.

## Predeclared variants
For each window 1s and 5s:
1. P95
2. P99
3. P95 + FLOW
4. P99 + FLOW
5. P95 + FLOW + LAG
6. P99 + FLOW + LAG

Followers:
- ETHUSDT
- SOLUSDT

## Future horizons
- 1s
- 5s
- 15s
- 30s
- 60s
- 120s

Future follower label:
first trade at/after t+h, requiring future-label delay <= 250 ms.

Direction:
same as BTC shock.

## Fee-only optimistic ceilings
Because trade prices ignore spread/slippage, these are upper bounds.

MEXC:
- taker/taker fee hurdle: 16 bps
- maker/maker fee hurdle: 12 bps

Report both.

## Survival rule
A follower × variant × horizon is CEILING_SURVIVOR only when:
- pooled n >= 30
- pooled mean fee-only MEXC maker/maker net > 0
- at least 2 of 3 date-level maker/maker mean nets > 0

No OOS opening from this run.
Any survivor requires executable follower-L2 validation before promotion.
