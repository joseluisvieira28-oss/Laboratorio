# CBETH-REDEMPTION-BASIS-001 — PRE-OUTCOME PREDICTOR DESIGN FREEZE V0.1

Frozen: 2026-09-27
Parent: SOURCE_GATE_FREEZE_V0.1
Freeze timing: BEFORE historical source-gate output, dense basis distribution, future returns or PnL.
Governance: RESEARCH-ONLY / OUTCOME-BLIND.

## Mechanism context

cbETH has an explicit protocol conversion-rate anchor and a separately traded market price.

The conversion anchor is oracle-updated by Coinbase, while market exchange price is independently determined.
Coinbase redemption can involve a material waiting period rather than frictionless immediate conversion.

Therefore this lab treats market-vs-conversion basis as an access/liquidity/risk-premium state, not a guaranteed arbitrage.

## Frozen daily observation clock

UTC observation timestamp:
17:00 UTC every calendar day.

Reason fixed pre-data:
the documented protocol conversion-rate process historically targets a daily update around 16:00 UTC; the 17:00 observation provides a deterministic post-update clock without using later outcomes.

If a source day cannot be resolved to the first canonical Ethereum block at or after 17:00 UTC, that day is invalid.
No nearest-day substitution.

## Frozen predictor

For day t at canonical observation block N_t:

protocol_t = exchangeRate_t / 1e18

market_t = exact WETH per cbETH from the source-qualified direct Uniswap V3 pool.

signed_basis_t =
market_t / protocol_t - 1

Interpretation:
- negative = market discount to protocol conversion anchor;
- positive = market premium.

No return or direction is implied yet.

## Frozen predictor calendar

Burn-in/source-only:
2023-01-01 through 2023-03-31

Calibration:
2023-04-01 through 2024-06-30

Discovery predictor-sample:
2024-07-01 through 2024-12-31

OOS:
2025-01-01 through 2025-12-31

Protected holdout:
2026-01-01 onward.

2026 is CLOSED.

## Frozen market-pool selection

If SOURCE_PASS identifies multiple qualifying direct cbETH/WETH pools:

select exactly one pool BEFORE dense census by this ordered source-only rule:
1. greatest count of valid positive-liquidity fixed historical sentinels;
2. then greatest finalized-block liquidity;
3. then lower fee tier as deterministic tie-break.

No outcome or basis magnitude may influence pool choice.

Once selected, the pool is immutable for this LAB_ID.

## Frozen calibration thresholds

Only after a complete valid calibration predictor census:

nearest-rank q10 and q90 over all valid calibration signed_basis values.

States:
- DISCOUNT_EXTREME when signed_basis <= q10;
- PREMIUM_EXTREME when signed_basis >= q90;
- NEUTRAL otherwise.

Both tails are mandatory.

Calibration is BLOCKED if:
- q10 >= q90;
- any required calibration day is missing/invalid;
- source pool changes;
- protocol or market state is imputed.

No q05/q95, q20/q80, z-score or raw-price rescue inside this LAB_ID.

## Frozen de-clustering

Discovery entry event occurs only on transition into a tail:
- current DISCOUNT_EXTREME and previous daily state != DISCOUNT_EXTREME;
- current PREMIUM_EXTREME and previous daily state != PREMIUM_EXTREME.

2024-06-30 predecessor must be evaluated by the same rule.

Consecutive same-tail days are one episode.

## Outcome-blind Discovery sample gate

Before any future basis or market-return outcome is opened:

PREDICTOR_SAMPLE_PASS requires:
- every 17:00 UTC Discovery day from 2024-07-01 through 2024-12-31 valid;
- >=20 transition events total;
- >=6 DISCOUNT_EXTREME;
- >=6 PREMIUM_EXTREME;
- zero source/provenance errors.

If source coverage fails:
PREDICTOR_SOURCE_BLOCKED.

If source passes but event count fails:
PREDICTOR_INSUFFICIENT_SAMPLE.

Neither classification opens an outcome.

## Pre-frozen mechanism direction and horizon

Only PREDICTOR_SAMPLE_PASS may open the following mechanism test.

Mechanism:
both extreme tails are expected to converge toward the protocol conversion anchor.

Primary horizon:
12 calendar days after event observation.

Rationale frozen pre-data:
the documented Coinbase redemption process can take up to 12 days.

For an entry signed_basis d_t and future signed_basis d_t12:

signed_closure_12d =
- DISCOUNT_EXTREME: d_t12 - d_t
- PREMIUM_EXTREME: d_t - d_t12

Positive signed closure supports convergence.

A 3-day horizon may be reported only as secondary diagnostic and cannot rescue the 12-day primary.

No ETH/USD or cbETH/USD directional trading return is primary in this mechanism test.

## Outcome partition firewall

Discovery mechanism outcomes:
entry dates only in 2024-07-01 through 2024-12-19 so the full 12-day primary remains inside 2024.

OOS 2025 remains unopened until a separately frozen Discovery PASS gate permits it.

2026 remains protected even though technically historical at execution time.

## No-rescue tree

- SOURCE_BLOCKED -> close exact lab.
- predictor census/calibration blocked -> close exact lab.
- PREDICTOR_INSUFFICIENT_SAMPLE -> close exact lab.
- mechanism Discovery FAIL -> close exact lab.
- mechanism Discovery PASS -> separate OOS authority required.

Do not:
- change q10/q90;
- drop a tail;
- change daily clock;
- change market pool;
- switch the 3-day diagnostic to primary;
- alter the 12-day primary;
- synthesize another venue;
- open 2025/2026 early.

## Trading firewall

No stage above authorizes:
- execution-cost fitting;
- PnL;
- position sizing;
- orders;
- exchange/wallet mutation;
- main merge.

Promotion credit = 0 until later governance explicitly permits otherwise.
