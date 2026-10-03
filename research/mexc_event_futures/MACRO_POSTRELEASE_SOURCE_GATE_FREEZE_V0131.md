# MACRO-POSTRELEASE-FWD-001 — PUBLIC SOURCE GATE FREEZE V0.13.1

Date: 2026-10-03
Status: PRE-OUTCOME / SOURCE-ONLY / FORWARD-ONLY
Parent: EVENT_CONDITIONED_EDGE_FREEZE_V0.13.md

## Scope

This family is economically distinct from chart-only signals because the observation window
is anchored to an official scheduled U.S. macro release.

Eligible releases in V0.13.1:
- U.S. Consumer Price Index (BLS CPI)
- U.S. Employment Situation (BLS jobs report)

No consensus forecast is used.

The earlier News Shock consensus hypothesis remains closed/source-blocked and is NOT reopened.
No Reuters/Bloomberg/economic-calendar consensus is introduced.

## Official event source

Primary schedule:
`https://www.bls.gov/schedule/news_release/bls.ics`

Release-page corroboration:
- CPI: `https://www.bls.gov/news.release/cpi.htm`
- Employment Situation: `https://www.bls.gov/news.release/empsit.htm`

All timestamps are interpreted in U.S. Eastern time using an IANA timezone implementation,
then converted to UTC with DST handled by the timezone library.

The schedule is mutable. Therefore every future event receipt must preserve the exact raw
ICS body hash used before the event, plus the parsed event identity/start time.

At event time, the current official BLS release page must corroborate the eligible release
and its embargo/publication timestamp. Failure => BLOCKED_EVENT_SOURCE.

## Public BTC/ETH market source

MEXC public standard-futures index websocket:
`wss://futures.mexc.com/edge`

Subscriptions:
- `sub.index.price` BTC_USDT
- `sub.index.price` ETH_USDT

No login, API key, private endpoint or order.

## Source gate requirements

PASS only if all are true in one bounded public run:

1. official BLS ICS returns a parseable calendar;
2. calendar contains both CPI and Employment Situation entries;
3. at least one future CPI or Employment Situation event is present after run time;
4. current CPI page is public/readable and identifiable as CPI;
5. current Employment Situation page is public/readable and identifiable as Employment Situation;
6. MEXC public index websocket yields at least one valid fresh BTC_USDT tick;
7. MEXC public index websocket yields at least one valid fresh ETH_USDT tick;
8. all raw source bodies/messages are preserved with SHA256 and receive times.

Verdicts:
- SOURCE_GATE_PASS
- PARTIAL_SOURCE
- SOURCE_BLOCKED

No macro direction or Event Futures outcome is scored in the source gate.

## Predeclared future signal rule — NOT ACTIVE UNTIL SEPARATE ACTIVATION FREEZE

If the source gate passes, a separate activation freeze MAY instantiate this exact rule:

For each eligible official release at time T:

1. Require a pre-event BLS schedule receipt whose parsed T was captured before T.
2. Require official current release-page corroboration after T.
3. Public index reaction source:
   - release index = first valid MEXC public index tick with server timestamp >= T;
   - reaction index = first valid tick with server timestamp >= T+5 minutes;
   - maximum lateness for each boundary = 5 seconds;
   - no candles/interpolation.
4. Reaction direction:
   - reaction index > release index => UP;
   - reaction index < release index => DOWN;
   - equality => NO_SIGNAL.
5. Condition source time = reaction tick server timestamp.
6. V0.13 Event Futures decision snapshot occurs only AFTER the immutable condition receipt.
7. Event Futures horizon = exactly 10 minutes.
8. Symbols: BTC_USDT and ETH_USDT independently.
9. Overlap: first only while unresolved.
10. Minimum N = 20 per symbol cell, preserving V0.13 absolute floor.
11. No payout filter beyond q>0.
12. 30-day windows are NOT used because event cadence is sparse; evaluation occurs only
    after the frozen N floor is reached, with no interim significance testing.

This is a follow-initial-reaction hypothesis. Direction, five-minute reaction window and
ten-minute Event Futures horizon may not be changed after the first outcome.

## Governance

- source gate opens zero outcomes;
- no consensus data;
- no historical macro outcome backtest in this version;
- no 2026 backfill;
- no post-outcome tuning;
- no live trading;
- no orders;
- no authenticated MEXC;
- no private/account/wallet access;
- no main merge.
