# CRYPTO LAB — PAYOFF FAST-START, distinct source-authority fork (frozen Oct 13, 2026)

## Why this fork exists
The PAYOFF 3-way forward gate froze 200 *post-boundary* hours of warmup. This is NOT economic evidence; the indicator SMA200 needs history, but it need not all be post-boundary. The earlier frozen BTC-CONVEX V0.2 already used historical pre-boundary warmup and generated post-start entry signals after just 4 new hours on 2026-09-24, as recorded in its publicly posted evidence.

**Nothing in this file retroactively modifies** PAYOFF 4R, NETSTOP or the current strict 200-new-hour source authority. This is a distinct prospective protocol proposed 2026-10-13 before the scheduled PAYOFF 2026-10-14 economic boundary.

## Immutable scientific rules
- Exactly three unchanged BTCUSDT 1h causal strategies: Parent V5, PAYOFF-40-10-BTC-001 and PAYOFF-FUNDING-NETSTOP-001 as previously frozen. No changes in entry, target, stop, time exit, fee, modeled funding, 2× or 10% capital-at-margin.
- Exactly one change: **signal indicator initialization** uses the last >=200 complete consecutive hourly historical bars ending immediately before the 2026-10-14T00:00Z boundary, from **already authorized BTC-CONVEX V0.2 research-public source observations**, not outcomes from a sealed holdout and not any newly unsealed protected dataset.
- The prior 200 bars must be traceable to an existing Parent V0.2 public data authorization and an immutable manifest (snapshot SHA, source record hashes, timestamps). If provenance or sealed 2026 constraints cannot be verified, **SOURCE_BLOCKED** and revert to strict existing 200h post-boundary protocol. Do NOT acquire/peek a sealed holdout to satisfy this.
- Pre-boundary market candles are solely indicator feature warmup; **zero PnL/trades/positions credited** before 2026-10-14 00:00 UTC. Starting equity 10489.94, state flat, first signal only after first full post-boundary bar closes; entry only at the subsequent 1h open.
- Require all complete consecutive hourly market bars, next-hour entry, public mark and funding coverage from economic boundary onward; no use of incomplete bars/future values. Pre-2026-10-14 historical funding is NOT processed as strategy cashflow.
- Still treat the post-boundary forward economic period separately from any retrospective 2020–25 result. No post-outcome tuning, changing leverage, fee rescue or making a selected model appear OOS. The 2026 sealed holdout remains protected.
- Official daily post-boundary archives plus verified preboundary warmup would permit first valid future shadow *evaluation* after Oct 14's first two completed hours (once source is available), without waiting 200 postboundary hours. Daily archives usually become accessible the next day; a complete Oct14 daily archive could first be checked Oct15. This is source-readiness only; trade closure may require weeks.
- Must report OPEN_UNRESOLVED and count any legitimately postboundary closed trades only after they exist, not on an arbitrary clock. Need venue-specific executable fills, spread, tick, min notional and liquidation proof before any trade GO.

## Safety
FAST_START_WARMUP_PROVENANCE_UNVERIFIED = NO_GO for source activation, even if synthetic unit tests pass. Never fabricate parent-authorized raw preboundary candles or assume the old V0.2 snapshot contains the required exact 200-hour segment. No auto-scheduler claimed; no orders/private endpoints/account/wallet/Render/main merge.

## Binary goal
Eliminate an **artificial 200h post-boundary warmup delay**, without pretending the economic forward validation itself needs no time or observations.
