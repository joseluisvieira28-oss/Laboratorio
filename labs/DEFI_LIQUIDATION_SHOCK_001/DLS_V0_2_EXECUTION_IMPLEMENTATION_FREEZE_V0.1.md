# DEFI-LIQUIDATION-SHOCK-001 — V0.2 EXECUTION IMPLEMENTATION FREEZE V0.1

Date: 2026-09-29
Status: FROZEN IMPLEMENTATION DETAIL / BEFORE V0.2 FUTURES PRICE ACCESS
Parent: DLS_V0_2_EXECUTABLE_VOLATILITY_DEVELOPMENT_FREEZE_V0.1.md

This resolves implementation details only. It does not change the frozen 60-configuration grid, event population, temporal split, thresholds, costs, or selection rule.

## Pre-event volatility

For event aligned minute A, define consecutive 1-minute returns from futures OPEN prices:

r_j = ln( OPEN(t_j) / OPEN(t_j - 1 minute) )

for t_j = A-60 minutes, ..., A-1 minute.

Exactly 60 returns require OPEN prices from A-61 through A-1 minutes.
No price at A or later is used in sigma60.

sigma60 = sqrt( mean(r_j^2) ).

If any required pre-event OPEN is missing, the event is ineligible for that configuration family.

## Trigger and fill

Reference entry price P_A = OPEN(A).

For k:
upper = P_A * exp(k*sigma60)
lower = P_A * exp(-k*sigma60)

Activation bars are minute bars with open timestamps:
A, A+1m, ..., A+(W-1)m.

First bar touching either threshold is the fill minute.

Long raw fill = upper.
Short raw fill = lower.

Slippage per side s:
- long entry execution price = raw fill * (1+s)
- short entry execution price = raw fill * (1-s)

Exit raw price = OPEN(first_fill_minute + H).

Adverse exit:
- long exit = raw exit * (1-s)
- short exit = raw exit * (1+s)

## Return and fees

One-unit notional, no leverage, no compounding.

Long gross return:
exit_exec / entry_exec - 1

Short gross return:
(entry_exec - exit_exec) / entry_exec

API taker fee:
8 bps per side.

Net return:
gross return - 0.0016

Slippage scenarios:
- 2 bps/side
- 5 bps/side
- 10 bps/side

Thus nominal round-trip stress labels remain 20 / 26 / 36 bps as frozen.

## Same-bar ambiguity

If both upper and lower thresholds are touched in the first trigger bar:
- compute long and short net returns independently under identical H/cost assumptions;
- primary result uses min(long_net, short_net);
- protocol attribution remains the source cascade protocol.

## Collision

Collision state is configuration-specific, independent of cost scenario because k/W/H determine fill and exit timestamps.

After a trade fills at F:
position is considered open until F+H.
Any later cascade with aligned A < F+H is ignored for that configuration.
A cascade with A >= F+H is eligible.

## Profit factor

profit_factor = sum(positive net returns) / abs(sum(negative net returns)).

If there are no negative returns and at least one positive return:
profit_factor = Infinity in memory and serialized as null plus profit_factor_infinite=true.

## Drawdown

Cumulative simple net return:
C_t = sum net_return_i in chronological trade order.

Maximum drawdown:
max_{t}( running_max(C_t) - C_t ).

No compounding.

## Protocol positive-PnL concentration

For each protocol:
positive_contribution = sum(max(net_return,0)).

concentration = max(protocol positive_contribution) / total positive contribution.

Eligibility requires concentration <= 0.80.

## Firewall

development_prices_allowed=2021-12-08..2024-12-31
2025_opened=false
2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
post_outcome_parameter_expansion=false
