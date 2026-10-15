# DUAL-LST-RV-001 — PRE-OUTCOME MECHANISM FREEZE V0.1

Frozen: 2026-09-27
Freeze timing: BEFORE authoritative V0.1B source result, before predictor census distribution, and before all future outcomes.

## Economic hypothesis

The direct rETH/wstETH market can deviate temporarily from the relative protocol-accounting NAV implied by:

- Rocket Pool ETH per rETH; and
- Lido protocol-accounting ETH per wstETH.

Because both legs are liquid staking tokens with common ETH beta, a relative-value state may isolate protocol-specific dislocation more cleanly than a single-LST ETH basis.

The frozen mechanism hypothesis is convergence of the signed relative-NAV dislocation toward zero.

## Frozen state direction

Using the pre-frozen q10/q90 states:

RETH_CHEAP_EXTREME:
d_N <= q10

Expected convergence:
d increases toward zero.

RETH_RICH_EXTREME:
d_N >= q90

Expected convergence:
d decreases toward zero.

Both tails are mandatory.
Neither tail may be discarded after outcomes.

## Frozen primary horizon

Primary:
N + 7,200 Ethereum blocks.

Secondary diagnostic:
N + 21,600 blocks.

The secondary horizon may not rescue a failed primary.

No alternate primary horizon may be selected after outcomes.

## Frozen primary outcome

For entry block N:

delta_d_7200 = d_(N+7200) - d_N

signed_closure_7200:

- RETH_CHEAP_EXTREME:
  +delta_d_7200

- RETH_RICH_EXTREME:
  -delta_d_7200

Positive signed_closure supports convergence toward relative protocol NAV.

Also retain descriptively:

closure_fraction_7200 =
signed_closure_7200 / abs(d_N)

when d_N != 0.

This is a mechanism-state outcome.
It is NOT PnL.

## Discovery entry region

24,000,000 <= N < 25,000,000.

The predictor sample gate must PASS before any N+7,200 or N+21,600 future state is opened.

## Frozen outcome-eligible sample minimum

After exact future-state availability:

- total valid events >= 20;
- RETH_CHEAP_EXTREME events >= 6;
- RETH_RICH_EXTREME events >= 6.

If boundary/source censoring reduces the sample below this:
MECHANISM_DISCOVERY_INSUFFICIENT_SAMPLE.

No threshold or date rescue.

## Frozen statistical gate

If the sample minimum passes:

1. pooled mean signed_closure_7200;
2. mean signed_closure_7200 for RETH_CHEAP_EXTREME;
3. mean signed_closure_7200 for RETH_RICH_EXTREME;
4. 10,000 deterministic event-row bootstrap resamples;
5. bootstrap seed = 20260927;
6. percentile 95% confidence interval of pooled mean.

MECHANISM_DISCOVERY_PASS requires ALL:

- pooled mean signed_closure_7200 > 0;
- bootstrap 95% lower bound > 0;
- cheap-tail mean > 0;
- rich-tail mean > 0.

Otherwise:
MECHANISM_DISCOVERY_FAIL.

The +21,600 diagnostic cannot alter the primary verdict.

## No-rescue rules

If Discovery fails, do NOT:

- invert convergence direction;
- drop one tail;
- switch q10/q90;
- change selected pool;
- change common-numeraire construction;
- use a synthetic market;
- change 7,200-block primary horizon;
- promote the 21,600-block diagnostic;
- select subperiods or clock filters.

## OOS / protected holdout

OOS:
25,000,000 <= entry block < 26,000,000.

Protected holdout:
entry block >= 26,000,000.

Only MECHANISM_DISCOVERY_PASS may permit a separate OOS authority.

Protected holdout remains sealed until a separately frozen OOS gate passes.

## Trading firewall

Even MECHANISM_DISCOVERY_PASS is not executable trading edge.

This freeze opens no:

- fee/slippage model;
- financing/borrow cost;
- actual long/short execution;
- PnL;
- position sizing;
- live orders;
- exchange/wallet mutation.

Promotion credit = 0.
