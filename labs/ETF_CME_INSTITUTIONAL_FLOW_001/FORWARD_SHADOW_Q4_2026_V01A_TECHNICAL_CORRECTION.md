# ETF-CME-INSTFLOW-001 — FORWARD SHADOW Q4 2026 — V0.1A TECHNICAL CORRECTION

Status: **FROZEN_PRE_OUTCOME / TECHNICAL_CORRECTION_ONLY**

Parent study: `ETF-CME-INSTFLOW-001-FORWARD-SHADOW-Q4-2026-V0.1`
Corrected study: `ETF-CME-INSTFLOW-001-FORWARD-SHADOW-Q4-2026-V0.1A`

## Why this correction exists

The original V0.1 checkpoint queried CFTC rows only from `2026-09-15` onward and then calculated deltas starting from the second returned prospective row. That makes the first allowed `2026-09-15` signal mechanically impossible because the immediately preceding weekly CFTC state is absent from the query. As a result, V0.1 can produce at most 13 prospective signals even though its frozen protocol declared `target_max_weeks = 14`.

The initial V0.1 source-only workflow run `34845220320` completed before this correction with:
- `cftc_rows_seen = 0`;
- `fully_elapsed_signal_windows = []`;
- `outcomes_fetched = false`;
- `new_market_outcomes_accessed = false`;
- `pre_freeze_2026_outcomes_accessed = false`.

Therefore this correction is made before any prospective CFTC row or BTC market outcome from the forward-shadow window was opened.

## Correction

V0.1A adds exactly one causal prior-state row solely for delta construction:
- required prior state: CFTC report date `2026-09-08`;
- the prior-state row may provide only `open_interest_all`, `noncomm_positions_long_all`, and `noncomm_positions_short_all` needed to compute the first `2026-09-15` delta;
- no BTC price/outcome associated with the prior-state row may be fetched or used;
- if the exact `2026-09-08` prior state is unavailable, the checkpoint fails closed.

For the first prospective row, V0.1A computes:

`delta_net_noncommercial = net_noncommercial_2026-09-15 - net_noncommercial_2026-09-08`

and preserves the original signal denominator:

`signal = delta_net_noncommercial / open_interest_t`

Later prospective rows use the immediately preceding prospective CFTC row exactly as intended by V0.1.

## Scientific design unchanged

No change to:
- CFTC dataset `6dca-aqww`;
- CME BTC contract code `133741`;
- non-commercial long/short category;
- expected positive sign;
- thresholds: none;
- z-score: false;
- winsorization: false;
- regime filter: false;
- alternate COT category: false;
- first allowed as-of date `2026-09-15`;
- last allowed as-of date `2026-12-15`;
- entry timing = as-of + 8 calendar days at/after BTCUSDT 00:00 UTC;
- exit = entry + 7 calendar days;
- latest allowed exit `2026-12-31`;
- base round-trip cost 10 bps;
- stress round-trip cost 20 bps;
- minimum evaluable weeks 12;
- all frozen success criteria;
- Tier effect = none automatic.

## Governance

V0.1 remains immutable historical evidence but is `SUPERSEDED_FOR_FORWARD_EXECUTION_BY_V0.1A` because of the pre-outcome source-state off-by-one defect. This is not a signal rescue, parameter change, market-outcome retest, or relaxation of any gate.

Research-only. No live trading. No exchange mutation. No orders. No main merge. No post-outcome tuning. No pre-freeze 2026 market outcomes. The V0.1A checkpoint remains source-only and may not fetch BTC outcomes.
