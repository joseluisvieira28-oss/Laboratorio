# DEFI-LIQUIDATION-SHOCK-001 — SIGNED RETURN V0.1 DEVELOPMENT FREEZE

Date: 2026-09-29
Branch: dls-signed-return-v01
Status: FROZEN BEFORE ANY SIGNED-RETURN MARKET OUTCOME IS OPENED

## Scientific parent authority

This experiment is a NEW hypothesis family. It is not a rescue or rerun of DLS V0.2 executable volatility.

Parent source authority:
- SIGNED_FLOW_SOURCE_CLOSEOUT_V0.1_2026-09-29.md
- Drift / liquidate_perp / January 2023 = SIGNED_FLOW_SOURCE_PASS
- canonical source population run 36525438771
- canonical artifact dls-drift-jan2023-signed-flow-population-v01
- artifact ID 11014134904
- artifact digest sha256:00468acecb8e0798ec56497f5c284965e65974c066d57b30546bff5143b93e15

Temporal semantics authority:
- run 36526742629
- classification DRIFT_2022_2024_SIGNED_SEMANTICS_TEMPORAL_PASS
- state_count = 134
- distinct_layout_count = 1
- artifact ID 11014578574
- artifact digest sha256:e30bf127e9ba8e008fc6fc29e03c32d9a52ed1ba3fe719ca19d9176b74a329bc

Historical Drift source at 9a1a83029e995807efe9e15b8a77f59d100fd33b proves:
- marketIndex 0 = SOL-PERP / baseAssetSymbol SOL
- marketIndex 1 = BTC-PERP
- marketIndex 2 = ETH-PERP

Only marketIndex 0 is admitted in V0.1 because the already-passed V0.2 execution source route provides an independently frozen Binance USDT-M SOLUSDT market-data route. No BTC/ETH venue mapping may be introduced after outcomes.

## Hypothesis

For source-proven realized Drift SOL-PERP liquidate_perp events, protocol-native realized signed flow has short-horizon continuation:

- SIGNED_BUY_PRESSURE_PROVEN => LONG SOLUSDT
- SIGNED_SELL_PRESSURE_PROVEN => SHORT SOLUSDT

Primary horizon = 5 minutes.

The 5-minute horizon is confirmatory: DLS V0.1 already established a direction-agnostic 5-minute volatility expansion. It is not selected from signed-return outcomes.

No reversal hypothesis is authorized in this family.

## Development population

Development source window:
2023-01-01T00:00:00Z <= event timestamp < 2023-02-01T00:00:00Z

Canonical signed source artifact above is the only event authority.

Admit only:
- canonical_market_index == 0
- status == PROVEN_REALIZED
- direction_label in {SIGNED_BUY_PRESSURE_PROVEN, SIGNED_SELL_PRESSURE_PROVEN}
- non-zero signed_base_asset_amount

PROVEN_NOT_REALIZED rows are reported but are not signals.

If any SOURCE_EVIDENCE_INCOMPLETE row occurs for marketIndex 0 in the same signal minute, that minute is fail-closed and excluded.

No amount threshold is allowed.
No event may be dropped based on later price movement.

## Signal aggregation

Signal minute M is floor(event timestamp to UTC minute).

For every source-complete realized event in M:
- BUY contributes +abs(signed_base_asset_amount)
- SELL contributes -abs(signed_base_asset_amount)

Net signed flow S_M is the sum.

- S_M > 0 => LONG candidate
- S_M < 0 => SHORT candidate
- S_M == 0 => no trade

Magnitude is recorded for audit only and is not a selection threshold or position-sizing input.

## Entry / latency

Entry timestamp A = M + 1 minute.

Entry reference price = Binance USDT-M SOLUSDT 1-minute bar OPEN at A.

This guarantees the trade decision occurs strictly after the event minute and prevents use of same-minute post-event OHLC information.

If the entry bar is missing, fail closed for that signal.

## Position rule

One position maximum.

Primary holding horizon H = 5 minutes.

Exit timestamp = A + 5 minutes.
Exit reference price = SOLUSDT 1-minute bar OPEN at exit timestamp.

While a position is open:
- later signal minutes are ignored;
- there is no pyramiding;
- there is no reversal;
- there is no TP/SL;
- there is no discretionary exit.

If a trade interval touches a standard Binance funding timestamp at 00:00, 08:00 or 16:00 UTC, exclude the trade instead of modeling funding.

## Costs

Use exactly the already-frozen V0.2 execution cost model:

Taker fee per side = 8 bps.

Primary adverse slippage per side = 5 bps.
Primary nominal round-trip fee+slippage = 26 bps.

Sensitivity only:
- 2 bps slippage per side => nominal 20 bps round trip
- 10 bps slippage per side => nominal 36 bps round trip

Sensitivity results cannot select or rescue the primary rule.

Execution math:
- LONG entry = open_A * (1 + slippage)
- LONG exit = open_exit * (1 - slippage)
- SHORT entry = open_A * (1 - slippage)
- SHORT exit = open_exit * (1 + slippage)
- fee is charged on both sides using the same V0.2 net-return function.

## Market-data source

Venue:
Binance USDT-M Futures

Instrument:
SOLUSDT

Granularity:
1 minute

Source:
data.binance.vision daily futures/um klines ZIP archives plus published CHECKSUM.

Every downloaded daily archive must:
- return HTTP 200;
- have a parseable 64-hex checksum;
- match SHA256 exactly;
- contain exactly one CSV member;
- have monotonic unique 1-minute timestamps;
- contain only rows within the expected UTC day.

Any hard source-integrity failure => SIGNED_RETURN_DEVELOPMENT_SOURCE_BLOCKED.

## Development adjudication

Primary metrics use only the primary 5 bps/side slippage scenario.

Minimum analyzable non-overlapping trade count:
30.

Primary gate requires ALL:
1. n >= 30
2. mean net return > 0
3. profit factor > 1.05
4. UTC-day block bootstrap 95% CI lower bound for mean net return > 0

Bootstrap:
- resampling unit = UTC day
- 10,000 replicates
- RNG seed = 260929
- percentile interval = 2.5% / 97.5%

If all pass:
SIGNED_RETURN_DEVELOPMENT_SURVIVES

Otherwise:
SIGNED_RETURN_DEVELOPMENT_NO_EDGE

If source integrity or canonical authority cannot be verified:
SIGNED_RETURN_DEVELOPMENT_SOURCE_BLOCKED

There is no alternate horizon, threshold, reversal mapping, amount filter, side filter or rescue grid in V0.1.

## Pre-frozen future gates

These boundaries are frozen now, before development outcomes.

If and only if development SURVIVES:

### OOS source / outcome window
2023-02-01T00:00:00Z <= event timestamp < 2023-04-01T00:00:00Z

Before OOS returns may be opened:
- source-only signed-flow population for this exact window must independently satisfy the existing source authority;
- implementation must be frozen against this document;
- no parameter may change.

OOS PASS must apply the exact development rule and costs, with no reselection.

### Holdout
2024-01-01T00:00:00Z <= event timestamp < 2025-01-01T00:00:00Z

Holdout remains closed until an OOS PASS and a separate immutable pre-holdout receipt.

2025 and 2026 remain protected and unopened in this family.

## Anti-tuning firewall

The already-observed signed-flow direction mix is source evidence, not a performance result.

Forbidden after this freeze:
- changing BUY=>LONG / SELL=>SHORT
- introducing BUY-only or SELL-only rules
- changing the 5-minute primary horizon
- adding magnitude thresholds
- changing minute aggregation
- changing latency
- changing overlap handling
- changing primary costs
- adding reversal/rescue variants
- choosing markets from observed returns
- opening OOS after a development failure
- opening holdout before OOS PASS

## Operational firewall

live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
market_2025_opened=false
market_2026_opened=false
oos_outcomes_opened=false
holdout_outcomes_opened=false
post_outcome_tuning=false
