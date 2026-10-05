# BINANCE-LISTING-FIRST-SECONDS-CASCADE-002 — FORWARD V0.1 PRE-OBSERVATION FREEZE
Date: 2026-10-05
Status: FROZEN BEFORE ANY FUTURE EVENT OBSERVATION

## Motivation
The closed BINANCE-LISTING-INFORMATION-CASCADE V2.0 2025 holdout rejected the frozen >=60s delayed-entry strategy as NO_EXECUTABLE_EDGE_HOLDOUT.

This is a NEW economic hypothesis, not a rescue or retuning of V2.0.

## Hypothesis
A Binance spot-listing announcement may create a measurable public-information propagation delay across already-trading external venues. A public observer may have a short but non-zero reaction window after first receiving the official announcement.

## Forward-only boundary
No historical 2025 or already-occurred 2026 event may be used to pass/fail this protocol.
Only announcements first observed AFTER activation of the collector count.

Historical outcomes may not be used for threshold selection.

## Announcement trigger
Primary trigger is PUBLIC, UNAUTHENTICATED official Binance announcement content.

Because the official Binance Announcements WebSocket requires API-key authentication/signing, it is OUT OF SCOPE for V0.1.

T_obs = local monotonic receive timestamp when the collector first observes a previously unseen official Binance spot-listing announcement from the public official surface.

The collector must persist:
- UTC wall-clock receive time
- monotonic receive time
- official announcement identifier/URL
- content hash
- parsed asset/ticker candidates
- collector build commit
- poll/request latency metadata

No claim is made that T_obs equals Binance internal publication time.

## Market-data trigger and venue policy
Primary market-data venue for V0.1:
BITGET SPOT PUBLIC WEBSOCKET.

Public trade stream is the primary tape.
Public best-bid/ask or shallow book stream is required for executable-price diagnostics when available.

No authenticated/private endpoint.
No account read.
No order placement.
No wallet.
No exchange mutation.

An observation is eligible only if the exact asset identity is already trading on Bitget before T_obs.

## Pre-trigger buffer
The collector must maintain a rolling market buffer BEFORE T_obs so the reaction can be measured without hindsight.

Required minimum pre-trigger buffer:
60 seconds of timestamped public market events.

## Frozen reaction buckets
Relative to T_obs:
- 0–1s
- 1–2s
- 2–5s
- 5–10s
- 10–30s
- 30–60s

Also report cumulative 0–5s, 0–10s, 0–30s, 0–60s.

No bucket may be added/removed after first eligible event.

## Frozen observables
For each eligible event:
- first trade timestamp after T_obs
- first BBO update timestamp after T_obs
- last pre-trigger trade
- mid/BBO at trigger when available
- signed and unsigned trade volume per bucket
- trade count per bucket
- VWAP per bucket
- return from last pre-trigger trade to bucket-end trade
- best-ask executable mark at +1s, +2s, +5s, +10s
- spread in bps at trigger/+1s/+2s/+5s/+10s when BBO is available
- maximum favorable/adverse excursion through +60s
- BTC-USDT contemporaneous return over identical buckets on the same venue
- asset return ex-BTC

## Shadow execution models — frozen BEFORE first event
Long-only information reaction hypothesis.

Four independent shadow entries:
A: first available best ask at or after T_obs + 250ms
B: first available best ask at or after T_obs + 500ms
C: first available best ask at or after T_obs + 1000ms
D: first available best ask at or after T_obs + 2000ms

If no valid best ask exists at/after the target latency within 500ms, that entry model is unavailable for that event.

Primary shadow exit for all models:
T_obs + 10 seconds, first available best bid at/after target within 500ms.

Secondary exits:
+5s and +30s.

Frozen cost stress is applied IN ADDITION to observed bid/ask crossing:
- primary: 20 bps total additional friction
- sensitivity: 10 bps and 40 bps

No live order is authorized.

## Discovery sample and gates
This is a prospective discovery phase, not a confirmatory holdout.

Minimum sample:
n >= 12 eligible future listing observations.

A latency model is a CANDIDATE SURVIVOR only if ALL:
- n >= 12
- median observed-crossing +10s net20 return > +0.50%
- positive hit rate >= 65%
- leave-one-out median net20 +10s > 0
- no single observation >35% of summed positive net20 returns
- median +10s gross return ex-BTC > 0
- median trigger spread <= 100 bps
- at least 10/12 observations have valid BBO-based entry and exit for that latency model

The four latency models are reported separately.
No selecting a latency after outcomes and pretending it was primary.
Any survivor requires a NEW pre-outcome confirmatory freeze before any later holdout.

## Failure semantics
- public announcement trigger cannot be observed reliably -> SOURCE_BLOCKED
- public market stream cannot maintain required buffer/timestamps -> SOURCE_BLOCKED
- n<12 -> COLLECTING
- n>=12 and no latency model passes all gates -> NO_EDGE_DISCOVERY
- one or more models pass -> SURVIVES_FORWARD_DISCOVERY

## Governance
Research-only.
Forward observation only.
No live trading.
No orders.
No private/authenticated exchange endpoints.
No account reads.
No wallets.
No merge to main.
No post-outcome tuning.
