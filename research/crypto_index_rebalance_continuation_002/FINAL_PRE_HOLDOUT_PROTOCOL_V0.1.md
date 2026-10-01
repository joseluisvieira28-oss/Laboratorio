# CRYPTO-INDEX-REBALANCE-CONTINUATION-002 — FINAL PRE-HOLDOUT PROTOCOL V0.1

Date: 2026-10-01
Status: FROZEN_PRE_OUTCOME / CONFIRMATORY HOLDOUT / RESEARCH ONLY
Branch: crypto-index-rebalance-continuation-v0.1

## Hypothesis
The parent study's apparent positive "post" effect was measured from the official Bitwise Results-page
date at 16:00 ET. Official Bitwise methodology instead places standard monthly reconstitution at
16:00 ET on the last NYSE Business Day, typically the following business/calendar day in the child sample.

New child hypothesis:
after the official Results state is available on the prior date, benchmark-tracking inventory pressure
continues in the ADD/REMOVE direction into the actual implementation boundary.

This is NOT a rescue of the parent's reversal hypothesis.

## Confirmatory universe
Exactly the 32 outcome-blind USD-M route-qualified legs from route identity:
a5411273d65be311d40fea168f3b616375cb41f23cf4322f353abffdef7216f0

Months:
- 2025-01
- 2025-07
- 2025-11
- 2026-02
- 2026-05
- 2026-07

2026-09 is excluded before outcomes because it overlaps the parent prospective September pilot.
No later addition of 2026-09 is allowed as rescue.

## Instruments
Binance USD-M perpetual futures:
- token leg = exact TICKERUSDT
- hedge leg = BTCUSDT
- equal absolute USD notional per leg

ADD:
LONG token / SHORT BTC

REMOVE:
SHORT token / LONG BTC

## Causal timing
Historical exact machine publication timestamps are unavailable.
To avoid treating the Results-page 16:00 ET as an instantaneous tradable publication tick, a fixed
pre-outcome delay is imposed.

Entry:
06:00:00 UTC on the implementation date.

Exit:
16:00:00 America/New_York on the same implementation date.

This places entry approximately 9-10 hours after the prior Results-page "As of 4:00pm ET" timestamp
and retains only the final implementation-day pressure window.

Price:
OPEN of the exact 1-minute USD-M Futures candle whose open timestamp equals the boundary.
No nearest candle. Missing exact boundary => DATA_BOUNDARY_INELIGIBLE.

## Gross pair return
For each leg:
token_ret = ln(token_exit/token_entry)
btc_ret   = ln(btc_exit/btc_entry)
sign = +1 ADD, -1 REMOVE

gross_signed_bps = sign * (token_ret - btc_ret) * 10,000

Positive = continuation in the benchmark-flow direction.

## Costs — frozen before prices
Current Binance regular-user USD-M USDT taker rate is 0.0500% = 5 bps per execution.

Equal-notional pair requires four executions:
token entry + BTC entry + token exit + BTC exit.

FEE_FLOOR = 20 bps round trip.

Because historical 1m OHLC does not reconstruct executable spread/depth/funding exactly:
BASE all-in reserve = 30 bps
- 20 bps fee floor
- 10 bps aggregate reserve for spread/slippage/funding/friction

STRESS all-in reserve = 50 bps
- 20 bps fee floor
- 30 bps aggregate reserve for spread/slippage/funding/friction

No fee discount, maker assumption, BNB discount or VIP status.

base_net_bps = gross_signed_bps - 30
stress_net_bps = gross_signed_bps - 50

## Statistical unit
Primary unit = change month.

Within each month, equally average every valid route-qualified leg.
No token weighting by observed performance.

Inference:
- 10,000 month-cluster bootstrap resamples
- seed 20261001
- statistic = mean month gross_signed_bps
- percentile 95% CI

## Minimum evidence
Before adjudication:
- >=24 valid event legs
- >=5 valid change months
- both ADD and REMOVE
- both 2025 and 2026
- >=2 valid legs in every retained month
- zero unresolved source conflicts

Failure => HOLDOUT_DATA_INSUFFICIENT.

## Mandatory survival gates — ALL required
A. mean month gross_signed_bps >= +50 bps
B. bootstrap 95% lower bound of mean month gross_signed_bps > 0
C. median month gross_signed_bps > 0
D. >= 4 positive-gross months
E. leave-one-month-out gross mean > 0 for >=80% of omissions
F. mean gross ADD legs > 0 AND mean gross REMOVE legs > 0
G. mean BASE net across all valid legs > 0
H. mean STRESS net across all valid legs > 0
I. >= 3 months have positive mean STRESS net
J. 2025 mean gross > 0 AND 2026 mean gross > 0
K. max absolute month contribution / sum absolute month contributions <= 40%

If all pass:
HOLDOUT_CONTINUATION_SURVIVES

If gross mechanism gates A-F/J/K pass but economic gates G-I fail:
HOLDOUT_MECHANISM_ONLY_COST_BLOCKED

Otherwise:
HOLDOUT_CONTINUATION_FAILED

## Anti-rescue
After market prices are opened:
- no entry-time change
- no exit-time change
- no switch back to parent 24h geometry
- no token deletion
- no month deletion
- no ADD-only / REMOVE-only rescue
- no spot substitution
- no alternate exchange
- no maker assumption
- no cost reduction
- no threshold or statistical-unit change
- no use of 2026-09 to rescue failure

Any changed design requires a new scientific identity and untouched evidence.

## Authority
Research only.
No live trading.
No orders.
No exchange mutation.
No main merge.
Passing this holdout would justify a separate execution-feasibility study, not live authority.
Trading authority: NONE.
