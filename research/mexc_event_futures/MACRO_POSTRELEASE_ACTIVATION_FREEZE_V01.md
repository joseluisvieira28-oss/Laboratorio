# MACRO-POSTRELEASE-FWD-001 — ACTIVATION FREEZE V0.1

Date: 2026-10-03
Status: FROZEN BEFORE FIRST MACRO V0.1 OUTCOME
Source gate: PASS
Research mode: SHADOW ONLY

## Authority

Parent protocol:
`EVENT_CONDITIONED_EDGE_FREEZE_V0.13.md`

Source gate:
- run `37128230979`
- artifact `11276120518`
- digest `sha256:ee66c4f07b6291fb03917c746c0076af8d18e0210e465fcee53beff308920129`

Rule file:
`MACRO_POSTRELEASE_RULE_V01.json`

Canonical rule hash:
`2e91d8375770b9e3d6a887813e17387eae83594c889988b3329e65a699f57af6`

## Eligible releases

Only official BLS:
- Consumer Price Index;
- Employment Situation.

No consensus forecast, surprise variable, Reuters/Bloomberg calendar, or retrospective macro backfill is part of V0.1.

## Signal formation

For each eligible official release with immutable release timestamp T:

1. pre-event BLS schedule evidence must already exist before T;
2. after T, the official BLS release page must corroborate the release;
3. for each symbol independently, define `release_index` as the first valid public
   MEXC `push.index.price` tick with server timestamp >= T and at most 5 seconds late;
4. define `reaction_index` as the first valid public tick with server timestamp >=
   T+300000 ms and at most 5 seconds late;
5. if reaction_index > release_index => signal UP;
6. if reaction_index < release_index => signal DOWN;
7. equality => NO_SIGNAL.

The immutable condition receipt is created only after the reaction tick exists.

## Event Futures shadow decision

Symbols:
- BTC_USDT
- ETH_USDT

Horizon:
- exactly 10 minutes.

Decision protocol:
- use the exact V0.13 fresh product/payout snapshot after condition creation;
- require product ONLINE;
- require exact 10m cycle;
- use actual direction-specific payout q observed for that event;
- first public index tick at/after payout response;
- payout/index local join <=5 seconds;
- condition age at decision <=5 seconds.

Expiry:
- first public index tick with server timestamp >= decision+10m;
- maximum lateness 5 seconds;
- no interpolation/candle substitute.

## Dedup / overlap

Signal identity:
`BLS_UID + symbol`.

Only one event per BLS release and symbol.

If a prior macro event for the same symbol is unresolved, a later signal is `SKIPPED_OVERLAP`.

## Evidence and statistics

Minimum N:
- 20 resolved non-blocked events per symbol cell.

No interim significance verdict before N=20.

When eligible for evaluation, use the V0.13 event-specific payout null, bootstrap and
Holm-Bonferroni rules unchanged.

## First eligible event

The first event allowed by this activation freeze is:

- kind: CPI
- BLS UID: `7d17bd53-87ad-4c74-a328-528f5e2b1e82`
- release UTC: `2026-10-14T12:30:00Z`

No release before this timestamp may be backfilled.

## Governance

- no post-outcome change to reaction window, direction, horizon, symbols or N;
- no consensus rescue;
- no historical 2026 scoring;
- no live trading;
- no orders;
- no login/private/account/wallet access;
- no merge to main.

Strongest possible future state remains:
`SURVIVES_FORWARD_SHADOW_GATE`.
