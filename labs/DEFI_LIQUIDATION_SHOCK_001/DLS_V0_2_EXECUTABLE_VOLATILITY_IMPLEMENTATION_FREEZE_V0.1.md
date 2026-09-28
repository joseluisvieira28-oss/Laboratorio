# DLS V0.2 — EXECUTABLE VOLATILITY IMPLEMENTATION FREEZE V0.1

Date: 2026-09-28
Status: FROZEN BEFORE FIRST FUTURES DEVELOPMENT PAYLOAD

## Pre-event volatility

For aligned cascade time A:
- use 61 consecutive completed 1-minute CLOSE observations ending at the bar A-1m;
- form 60 close-to-close log returns;
- sigma60 = sqrt(mean(r_i^2));
- no mean subtraction;
- any missing required bar => NO_TRADE_INSUFFICIENT_PRE_EVENT_VOL.

Reference price:
P_A = OPEN of the 1-minute bar at A.

## Activation window

For W minutes, inspect bars with open timestamps:
A, A+1m, ..., A+(W-1)m.

The first bar touching either frozen threshold is the trigger bar.

Upper touch:
HIGH >= P_A * exp(k*sigma60)

Lower touch:
LOW <= P_A * exp(-k*sigma60)

## Entry

Primary cost scenario:
- taker fee = 8 bps per side;
- adverse slippage = 5 bps per side.

Sensitivity:
- adverse slippage = 2 bps / side;
- adverse slippage = 10 bps / side.

Long fill:
upper_trigger * (1 + slippage)

Short fill:
lower_trigger * (1 - slippage)

If both thresholds touch in the first trigger bar:
- compute long and short under the exact same timed exit;
- primary result uses the LOWER net return;
- mark ambiguous=true.

## Exit

Exit timestamp:
trigger_bar_open_timestamp + H minutes.

Exit uses OPEN at that exact timestamp.

Long adverse exit:
exit_open * (1 - slippage)

Short adverse exit:
exit_open * (1 + slippage)

Missing exit OPEN => NO_TRADE_MISSING_EXIT_BAR.

## Funding-boundary rule

V0.2 development V0.1 does not model historical funding cashflows.

To prevent unmodeled funding from entering PnL, any prospective trade whose interval from trigger-bar open through exit timestamp includes a standard 8-hour funding boundary at 00:00, 08:00 or 16:00 UTC is:

NO_TRADE_FUNDING_BOUNDARY

This exclusion is timestamp-only and is applied before PnL inspection.

## Fee accounting

fee = 0.0008 per side.

For entry price E and adverse exit price X:

Long gross return:
X/E - 1

Short gross return:
1 - X/E

Round-trip fee deduction, expressed on entry notional:
fee + fee*(X/E)

Net return:
gross_return - round_trip_fee_deduction

No leverage, compounding, funding, borrow cost or liquidation mechanics are included in V0.2 development V0.1.

The maximum H is 60 minutes specifically to avoid introducing a funding-rate model in this first executable-volatility test.

## Position collision

One open position per configuration.

Sort cascades by T0 then cluster_id.
If cascade aligned A is strictly before current position exit timestamp:
IGNORE_COLLISION_ACTIVE_POSITION.

At exactly the prior exit timestamp the new cascade is eligible.

## Metrics

For each k/W/H/slippage configuration:
- eligible source cascades;
- trades;
- collision ignores;
- no-breakout count;
- insufficient-vol count;
- missing-exit count;
- ambiguous trade count;
- mean net return;
- median net return;
- win rate;
- profit factor = sum(positive net returns) / abs(sum(negative net returns));
- cumulative simple net return = sum(net returns);
- max drawdown computed on the non-compounded cumulative simple-return path;
- per-fold and per-protocol metrics.

Profit factor:
- infinite if losses sum exactly zero and positive gains exist;
- zero if no positive gains.

## Folds

Fold 1:
2021-12-08T00:00:00Z <= A < 2023-01-01T00:00:00Z

Fold 2:
2023-01-01T00:00:00Z <= A < 2024-01-01T00:00:00Z

Fold 3:
2024-01-01T00:00:00Z <= A < 2025-01-01T00:00:00Z

## Selection

Apply DLS_V0_2_EXECUTABLE_VOLATILITY_DEVELOPMENT_FREEZE_V0.1.md exactly.

No unlisted parameter may be tested after results.

## Firewall

2025_protected_oos_opened=false
2026_final_holdout_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
