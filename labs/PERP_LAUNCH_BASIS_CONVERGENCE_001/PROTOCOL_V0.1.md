# PERP-LAUNCH-BASIS-CONVERGENCE-001 — V0.1

Status: FROZEN PRE-DISCOVERY / RESEARCH ONLY
Branch: perp-launch-basis-convergence-v0.1

## Source authority
Reuse immutable source identity from PERPETUAL-LAUNCH-SHOCK-001 source gate:
- source MVE: PLS-BINANCE-USDTM-LAUNCH-001
- SOURCE_DATA_PASS
- 170 qualified launches
- 83 events in 2023
- 87 events in 2024
- exact event timestamp = frozen Binance USD-M perpetual first_open_time
- exact-symbol Binance Spot USDT market existed strictly before the perpetual launch

The predecessor opened 2023 intensity outcomes only. Its frozen sequential design explicitly kept 2024 market values unopened after Discovery failed.

## Economic mechanism
At launch, leveraged demand can make the new perpetual trade at a premium to the pre-existing spot market. A directly tradable convergence trade is:

- if the perpetual is at a positive premium after the first five complete 1m bars,
- LONG equal-USD token spot
- SHORT equal-USD token USD-M perpetual
- hold 60 minutes
- exit both legs simultaneously.

Negative/zero basis => NO TRADE. No spot borrowing is required.

## Frozen timing
For each launch event at T0:
- require exact contiguous 1m Spot and USD-M perpetual bars;
- observe first five complete minutes T0..T0+5m;
- entry price on each leg = close of the fifth 1m bar (bar open T0+4m);
- entry decision uses only information available at that close;
- basis_entry_bps = 10000 * ln(perp_entry / spot_entry);
- trade iff basis_entry_bps > 0;
- exit price = close exactly 60 minutes after entry close (bar open T0+64m);
- no intra-window stop/target.

## Gross pair return
For executed trades:

gross_pair_bps =
10000 * [ln(spot_exit/spot_entry) - ln(perp_exit/perp_entry)]

Positive = profitable convergence for LONG spot / SHORT perp.

No-trade events contribute zero to the all-eligible portfolio return.

## Costs
Inherited unchanged from predecessor strategy MVE PLS-OOS-ORBREAKOUT-001:
- BASE = 60 bps all-in completed pair trade
- STRESS = 160 bps all-in completed pair trade

These reserves cover four trading legs, ordinary slippage and funding reserve.
No cost reduction after outcomes.

Executed trade net:
- base_net_bps = gross_pair_bps - 60
- stress_net_bps = gross_pair_bps - 160

No-trade event net = 0.

## Sequential design
DISCOVERY = all 2023 source-qualified events only.
OOS = all 2024 source-qualified events only.

2024 may be opened only if every Discovery promotion gate passes.
If Discovery fails: STOP and preserve 2024 unopened.

## Discovery/OOS minimum evidence
- >=60 source-eligible events with complete paired windows
- >=25 executed positive-premium trades
- zero unresolved event/source conflicts

## Primary promotion gate — ALL required
Computed over the phase:
1. mean STRESS net across ALL eligible events > 0
2. UTC-launch-date cluster bootstrap 95% CI lower bound of mean STRESS net > 0
3. median STRESS net among executed trades > 0
4. STRESS hit rate among executed trades >= 52%
5. STRESS profit factor among executed trades >= 1.20
6. mean BASE net across ALL eligible events > 0

Bootstrap:
- cluster = UTC launch date
- replications = 10,000
- seed = 20261001
- confidence = 95%

## Classification
Discovery:
- BASIS_CONVERGENCE_SURVIVES_DISCOVERY
- NO_BASIS_CONVERGENCE_EDGE
- INSUFFICIENT_SAMPLE
- SOURCE_OR_TECHNICAL_BLOCKED

OOS, only if Discovery survives:
- OOS_BASIS_CONVERGENCE_SURVIVES
- NO_EXECUTABLE_OOS_EDGE
- INSUFFICIENT_OOS_SAMPLE
- SOURCE_OR_TECHNICAL_BLOCKED

## Anti-rescue
After 2023 outcomes open:
- no entry delay change
- no hold change
- no basis threshold beyond >0
- no magnitude filter
- no winner-symbol subset
- no side inversion
- no alternative spot/perp venue
- no session filter
- no cost reduction
- no stop/target optimization
- no 2024 opening after failed Discovery

Any changed design requires a new lab ID and new untouched holdout.

## Authority
Research only.
No live trading.
No orders.
No authenticated exchange access.
No exchange mutation.
No merge to main.
Trading authority: NONE.
