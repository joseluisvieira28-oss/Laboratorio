# DEFI-LIQUIDATION-SHOCK-001 — V0.2 EXECUTABLE VOLATILITY DEVELOPMENT FREEZE V0.1

Date: 2026-09-28
Branch: dls-v02-executable-volatility-v01
Status: FROZEN DEVELOPMENT CONTRACT / 2025-2026 PROTECTED

## Inherited evidence

V0.1 terminal classification: SURVIVES_OOS.

Frozen V0.1 claim:
completed on-chain liquidation cascades are followed by larger near-term absolute market moves than prospectively matched non-event controls.

V0.2 does not reinterpret V0.1 as directional alpha.

## V0.2 question

Can the already-proven post-liquidation volatility expansion be converted into a mechanically executable, direction-neutral breakout strategy with positive net expectancy after conservative fees and slippage?

## Temporal governance

Development:
- already-open 2021-2024 source/outcome period only.
- no claim of untouched validation from these years for V0.2.

Protected OOS:
- 2025 remains CLOSED until one V0.2 configuration is frozen.

Protected final holdout:
- 2026 remains CLOSED until a valid 2025 OOS pass and a new explicit authority.

No 2025/2026 market payload may be downloaded by the V0.2 development workflow.

## Canonical event trigger

Use the V0.1 canonical 60-second source cascade census.
For every directly mapped SOL market cascade:
- T0 = frozen completed-cascade T0.
- A = first exact UTC minute boundary >= T0.

No event membership, T0 or mapping may be changed from V0.1 using execution outcomes.

## Development execution market

Primary development market candidate:
BINANCE USDT-M SOLUSDT perpetual.

Reason:
- direct SOL/USDT executable derivative;
- public deterministic historical data route can be independently source-gated;
- allows symmetric long/short breakout testing.

This does NOT establish live venue authority for MEXC or any other venue.

A SOURCE PASS is required before execution-data payload access.

## Execution-cost authority

The initial conservative cost stress uses the current published MEXC API Futures general taker fee as an external executable-cost reference:
- taker fee per side = 0.08% = 8 bps.

Bracket entries and timed exits are modeled as taker/taker.

Pre-frozen adverse slippage scenarios per side:
- 2 bps
- 5 bps
- 10 bps

Round-trip all-in cost scenarios:
- 20 bps = 8+2 bps per side
- 26 bps = 8+5 bps per side
- 36 bps = 8+10 bps per side

The primary development selection uses the 26 bps round-trip scenario.
20 bps and 36 bps are sensitivity stresses.
A later live venue must re-bind its actual account/API fees before trading.

## Causal volatility scale

Before entry:
- use only completed 1-minute bars strictly before A;
- compute 60-minute log-return RMS:
  sigma60 = sqrt(mean(r_1m^2)) over the 60 one-minute returns ending immediately before A.

If fewer than 60 complete pre-event returns exist:
NO_TRADE_INSUFFICIENT_PRE_EVENT_VOL.

## Frozen development grid

Symmetric log-price breakout distance:
k in {0.25, 0.50, 0.75, 1.00, 1.50}

Upper trigger:
P_A * exp(+k * sigma60)

Lower trigger:
P_A * exp(-k * sigma60)

Activation window W after A:
W in {5, 15, 30} minutes.

Timed holding horizon H after first fill:
H in {5, 15, 30, 60} minutes.

Total development grid:
5 * 3 * 4 = 60 configurations.

No other k/W/H value may be introduced after viewing this grid's results.

## Fill rule

Use 1-minute OHLC bars.

For each minute in the activation window:
- upper trigger touched if HIGH >= upper trigger;
- lower trigger touched if LOW <= lower trigger.

If exactly one side is touched first:
- enter that side at trigger price plus adverse entry slippage.

If both sides are touched in the same first-trigger minute:
- path ordering is unknowable at 1-minute resolution;
- compute both possible trade directions under the same exit rule;
- record the WORSE net PnL as the primary conservative result;
- record ambiguity rate.

If no side is touched inside W:
NO_TRADE_NO_BREAKOUT.

## Exit rule

No stop/take-profit optimization in V0.2 development V0.1.

Exit exactly H minutes after the first trigger-minute open boundary using the next eligible 1-minute OPEN at the exit timestamp.

Apply adverse exit slippage.
No exit may cross 2025-01-01 in development.

## Position-collision rule

One SOL position maximum at a time for each candidate configuration.

Sort source cascades by T0.
Once a configuration has an open position:
- ignore later cascade triggers until the position exits.

This is a capital/execution rule, not an outcome-based filter.

## Development metrics

For every configuration and cost scenario report:
- eligible cascades;
- trades;
- no-trade rate;
- ambiguous-first-bar rate;
- gross mean return/trade;
- net mean return/trade;
- median net return;
- win rate;
- profit factor;
- cumulative simple net return at one-unit notional without compounding;
- maximum cumulative-return drawdown;
- trades by protocol family;
- results by development fold.

Development folds:
1. 2021-12-08 through 2022-12-31
2. calendar 2023
3. calendar 2024

## Frozen robust selection rule

Primary cost scenario: 26 bps round trip.

A configuration is ELIGIBLE_TO_FREEZE_FOR_2025 only if:
1. >= 500 total development trades;
2. net mean return > 0 overall;
3. net mean return > 0 in all three development folds;
4. profit factor > 1.05 overall;
5. no single protocol family contributes > 80% of total positive net PnL;
6. ambiguous-first-bar rate <= 10%.

Among eligible configurations select deterministically:
1. highest minimum fold net mean return;
2. then highest overall net mean return;
3. then lower k;
4. then shorter W;
5. then shorter H.

If none qualify:
V0.2 DEVELOPMENT_NO_EXECUTABLE_EDGE.

No rescue by new parameters after results.

## 2025 OOS

Do NOT open in this development authority.

If one configuration qualifies, create a separate pre-2025 OOS freeze that binds:
- exact k/W/H;
- exact market and data source;
- exact fee/slippage assumptions;
- exact fill/collision rules;
- OOS statistical gate.

Only then may 2025 be opened.

## Live firewall

live_trading=false
orders=false
wallets=false
exchange_mutation=false
main_merge=false
2025_opened=false
2026_opened=false
post_2025_tuning=false
