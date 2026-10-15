# CCLM-002 DISCOVERY IMPLEMENTATION ADDENDUM V0.1A

Frozen: 2026-09-25
Parent: CCLM_002_PRE_OUTCOME_DISCOVERY_FREEZE_V0.1
Outcome access at freeze: CLOSED

This addendum resolves implementation ambiguity only. It does not change the
predictor, threshold, dates, target, horizon, null, p-value or survival rules.

## Partition-boundary rule

A sample belongs to one scientific partition only if the complete primary
forward target lies inside that same partition.

For the primary 4h decision:
- Discovery trigger is eligible only if entry timestamp t and t+4h are both
  inside 2023-05-01 through 2023-12-31 UTC.
- OOS trigger is eligible only if t and t+4h are both inside 2024-01-01 through
  2024-06-30 UTC.
- Protected holdout follows the same rule if ever authorized.

Secondary descriptive horizons 1h / 12h / 24h are each reported only for
samples whose own target endpoint remains inside the active partition.

No price beyond a partition boundary may be used to complete a sample from the
earlier partition.

## Hourly market timestamp convention

Binance 1h spot kline:
- open_time defines UTC hour h;
- close value is interpreted as the complete close for that hour;
- scientific timestamp for that close is open_time + 1h.

CCTP settlement flow in UTC hour h is finalized at the end of h.
Entry t is therefore the close timestamp at that same hour boundary, exactly as
required by the parent freeze.

## Null implementation

The parent freeze requires a within-calendar-month circular shift of the entire
hourly flow series.

For each of exactly 10,000 permutations:
1. for every calendar month independently draw one integer-hour offset uniformly
   from the inclusive set [48, month_hours - 48];
2. circularly rotate that month's RAW signed hourly flow by that offset;
3. concatenate months in original calendar order;
4. recompute from the shifted raw flow:
   - causal prior-window median;
   - causal MAD;
   - robust_z;
   - abs(z)>=3 trigger rule;
   - 6h de-clustering;
5. compute the same primary mean signed 4h relative return at the shifted
   accepted trigger hours.

It is forbidden to shift precomputed z-scores or trigger timestamps instead of
the raw hourly flow.

## Deterministic RNG

Use NumPy Generator(PCG64(seed=20260924)).
Offsets are integer hours and the upper bound is inclusive.

## Insufficient null samples

A permutation with zero eligible de-clustered trigger samples has null statistic
defined as NaN and is excluded only from the numerical comparison denominator.

The empirical p-value remains:
(1 + count(valid null_stat >= observed)) / (1 + valid_null_count)

The parent freeze specified 10001 because 10,000 permutations were expected to
be valid. If any null is invalid, the receipt MUST disclose valid_null_count and
the adjusted exact denominator above. No replacement draws are allowed.

## Predictor viability firewall

If the separate outcome-blind predictor viability gate returns fewer than 30
independent Discovery triggers, classify INSUFFICIENT_SAMPLE and do not open any
price outcome. This addendum cannot override that stop.
