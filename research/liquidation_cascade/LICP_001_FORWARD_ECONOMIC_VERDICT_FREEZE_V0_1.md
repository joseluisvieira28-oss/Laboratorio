# LICP-001 — FORWARD ECONOMIC VERDICT FREEZE V0.1

Date: 2026-10-05
Status: FROZEN BEFORE ANY FORWARD OUTCOME RECEIPT WAS INSPECTED
Branch: liquidation-cascade-propagation-v0.1

## Integrity statement

This decision rule is frozen while the first technically corrected forward observer is still in progress.
No forward outcome receipt, post-trigger return, PnL, MFE, MAE, hit-rate, mean, median, or horizon result from the 2026-10-05 forward epoch was inspected before this freeze.

The failed earlier observer run exited on Python import before observation and produced no outcome receipt.

## Purpose

Prevent horizon, target, family, cost, and sample-size selection after outcomes are observed.

## Primary verdict sample

Use exactly the first 20 independent eligible `BTC_CONFIRMED` cascade episodes after the numeric trigger freeze, subject to:
- episodes span at least 3 distinct UTC dates;
- existing 120-second episode de-duplication remains unchanged;
- primary target is `BTC_USDT`;
- primary horizon is 60 seconds;
- entry/exit BBO semantics remain exactly those in `LICP_001_PROPAGATION_OUTCOME_PROTOCOL_FREEZE_V0_1.md`;
- direction remains forced-flow continuation: SELL => SHORT, BUY => LONG;
- base MEXC API taker/taker fee hurdle = 16 bps round trip;
- stress fee hurdle = 32 bps round trip (2x base costs);
- at least 18 of the first 20 episodes (90%) must have a complete valid BTC_USDT 60s outcome. Missing/stale/crossed observations are never backfilled.

If fewer than 20 episodes or fewer than 3 UTC dates exist, state = `FORWARD_INSUFFICIENT`.
If primary-outcome coverage is below 90%, state = `BLOCKED_DATA_QUALITY`, not NO_EDGE.

## Primary economic metrics

For each valid primary episode:
- `base_net_bps = mexc_taker_net_bps` from the frozen execution math;
- `stress_2x_net_bps = taker_gross_bps - 32`.

Across the valid primary sample compute:
- arithmetic mean base_net_bps;
- median base_net_bps;
- arithmetic mean stress_2x_net_bps;
- fraction of base_net_bps > 0.

No alternative horizon or target may replace the primary test.

## Verdict rule

`SURVIVES_FORWARD_CANDIDATE` only if ALL are true:
1. mean base_net_bps > 0;
2. median base_net_bps > 0;
3. mean stress_2x_net_bps > 0.

Otherwise, once the minimum sample/date/coverage gates are satisfied:
`NO_EDGE`.

This is intentionally stringent. It tests whether the forced-flow continuation effect is not merely positive on average under base fees but remains economically positive under a 2x API-cost stress.

## Secondary diagnostics — non-rescue only

The following may be reported descriptively but may NOT rescue a failed primary verdict:
- BTC_USDT horizons 1s / 2s / 5s / 15s / 30s;
- ETH_USDT and SOL_USDT outcomes;
- `ALT_SECOND_WAVE` family;
- maker/maker ceiling;
- OI context;
- BUY-vs-SELL splits.

If a secondary result appears promising after a primary NO_EDGE, it requires a new economically distinct hypothesis and a new prospective freeze before testing.

## Fee authority

MEXC announced API Futures taker fees of 0.08% per side effective 2026-06-01.
Therefore 16 bps taker/taker round trip remains the canonical executable API hurdle for this freeze.

## Protected actions

Authorized:
- public forward observation;
- immutable artifact persistence;
- deterministic aggregation;
- first-20 verdict under this rule.

Not authorized:
- orders;
- exchange authentication;
- exchange mutation;
- wallets/capital;
- merge to main;
- post-outcome threshold/horizon/target tuning.
