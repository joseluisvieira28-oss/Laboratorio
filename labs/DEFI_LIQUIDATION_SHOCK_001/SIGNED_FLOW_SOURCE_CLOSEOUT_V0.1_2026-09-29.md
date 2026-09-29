# DEFI-LIQUIDATION-SHOCK-001 — SIGNED FLOW SOURCE CLOSEOUT V0.1

Date: 2026-09-29
Branch: dls-signed-flow-authority-v01

## Terminal classification for the first authorized protocol/class

DRIFT / liquidate_perp / January 2023:

SIGNED_FLOW_SOURCE_PASS

This is a SOURCE AUTHORITY PASS only.
It does not prove predictive returns, profitability, executable edge, or live-trading authority.

## Canonical authority chain

- SIGNED_FLOW_SOURCE_AUTHORITY_FREEZE_V0.1.md
- DRIFT_LIQUIDATION_EVENT_LOG_ROUTE_CALIBRATION_FREEZE_V0.1.md
- DRIFT_JAN2023_SIGNED_FLOW_SEMANTICS_CALIBRATION_FREEZE_V0.1.md
  - freeze commit d28249b60a3688db3dfb0bf3bd444e0f7c0c0b9a
- first calibration run 36525100147
  - preserved BLOCKED because one selected successful instruction had no realized LiquidationRecord
  - two references already produced exactly bound positive signed base deltas
- DRIFT_JAN2023_REALIZED_EVENT_POPULATION_FREEZE_V0.1.md
  - freeze commit 3dd509d9d177eb65b43a8926b0a58b60c9a39a80
  - corrected the scientific unit from successful instruction calls to realized events
  - thresholds were not changed
- population run 36525438771
  - workflow conclusion SUCCESS
  - head 2182d0349c8283b84caa6e2530d4dcf911357b81
  - artifact dls-drift-jan2023-signed-flow-population-v01
  - artifact ID 11014134904
  - digest sha256:00468acecb8e0798ec56497f5c284965e65974c066d57b30546bff5143b93e15

## Population result

Canonical liquidate_perp instruction candidates: 3,179

Census:
- PROVEN_REALIZED: 2,237
- PROVEN_NOT_REALIZED: 920
- SOURCE_EVIDENCE_INCOMPLETE: 22
- CONTRADICTION: 0

The 920 proven-not-realized instructions are supported by the historical protocol early-return
condition `max_base_asset_amount_allowed_to_be_transferred == 0`; they are reported but are not
realized liquidation events.

Realized-event source coverage:
- R = 2,237
- I = 22
- (R-I)/R = 0.9902611775121736
- required >= 0.95
- PASS

Unique deterministic direction among non-incomplete realized events:
- SIGNED_BUY_PRESSURE_PROVEN: 2,208
- SIGNED_SELL_PRESSURE_PROVEN: 29
- deterministic direction rate = 1.0
- required >= 0.90
- PASS

Contradictions:
- 0
- required 0
- PASS

Therefore Drift liquidate_perp satisfies the frozen family source-authority rule.

## Economic interpretation authorized

For historical January-2023 Drift liquidate_perp realized events only:
- positive LiquidatePerpRecord.base_asset_amount is protocol-native realized BUY pressure;
- negative LiquidatePerpRecord.base_asset_amount is protocol-native realized SELL pressure.

This interpretation is derived from historical transaction/program semantics, not future returns.

The observed 2,208 / 29 imbalance is descriptive source evidence only.
It must not be treated as a profitable LONG rule without a separately frozen signed-return experiment.

## Other families

Save0c remains source-evidence PARTIAL/BLOCKED for directional labeling:
complete realized token-transfer evidence was observed, but same-transaction evidence did not establish
a market swap/execution route. Do not infer sell pressure merely from collateral transfer.

No claim is made here that Marginfi, Kamino, Save11, or all Drift periods are SIGNED_FLOW_AUTHORIZED.
Each requires its own frozen source-evidence adjudication before use.

## Next scientific authority

A future signed-return experiment may now be designed for the authorized Drift protocol/class.
Before any price outcomes are opened, freeze:
- exact event population and date splits;
- aggregation/cascade rule;
- mapping from signed flow to LONG/SHORT hypothesis;
- market/venue/source;
- entry timestamp and latency rule;
- horizon(s);
- costs/slippage if execution is tested;
- development/OOS/holdout boundaries;
- deterministic selection/adjudication gates.

Do not use the 2,208/29 imbalance to tune those parameters.

## Firewall

2025_market_outcomes_opened=false
2026_market_outcomes_opened=false
signed_return_outcomes_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
