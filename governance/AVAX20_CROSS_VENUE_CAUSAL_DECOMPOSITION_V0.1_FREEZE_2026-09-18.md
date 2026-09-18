# AVAX20 CROSS-VENUE CAUSAL DECOMPOSITION V0.1 — FREEZE — 2026-09-18

Status: FROZEN_BEFORE_OFF_DIAGONAL_OUTCOMES_OR_SIGNAL_CONCORDANCE
Branch: avax20-cross-venue-causal-decomposition-v0.1
Parent candidate: CED1D-0031 — AVAXUSDT Momentum 20D CONTINUATION H1
Parent authority branch: ced-1d-v3-byte-recovery-2026-09-17
OKX replication authority branch: cross-venue-diamond-replication-002-avax20

## Question

Determine whether the transferred AVAX20 effect is carried by the signal itself across venues, rather than merely producing similar same-venue aggregate economics.

## Immutable candidate identity

- family: A_MOMENTUM
- symbol identity: AVAX / USDT-margined perpetual
- lookback: 20 calendar days
- direction rule: CONTINUATION
- horizon: 1 day
- signal implementation: exact CED-1D-V1-RUNNER-FREEZE-V0.3
- V0.3 ZIP SHA256: df625d0d4a05c55ba34ca51514d31fd61636ff0a823567585c2d02afa0877958
- hypotheses.py SHA256: dc52cdc16aee0ba586ec7081a39ce68d62c5544e9bd27186255b4d9a87368693
- BASE nonfunding round-trip cost: 14 bps
- STRESS nonfunding round-trip cost: 20 bps
- one-active-trade / overlap semantics: exact parent semantics
- inference weeks: 2025-01-06 inclusive through 2025-12-29 exclusive
- 2026+ forbidden

## Frozen 2x2 matrix

Signal source A determines:
1. completed daily information set;
2. signal day;
3. direction;
4. parent entry-day / exit-day schedule;
5. overlap blocking.

Execution venue B determines:
1. D+1 00:01 UTC entry reference;
2. D+2 00:01 UTC exit reference;
3. raw venue return;
4. venue-specific actual funding;
5. venue-specific mark-price settlement bound;
6. BASE/STRESS funded economics.

Quadrants:
- BINANCE_SIGNAL__BINANCE_EXECUTION
- BINANCE_SIGNAL__OKX_EXECUTION
- OKX_SIGNAL__BINANCE_EXECUTION
- OKX_SIGNAL__OKX_EXECUTION

No quadrant may be deleted or substituted after outcomes.

## Source authorities

BINANCE:
- exact frozen 2025 1m source manifest V0.2 and SHA256 checks;
- exact funding-rate + mark-price interval source gate V0.4;
- AVAXUSDT USD-M perpetual.

OKX:
- exact frozen bulk historical candlestick/funding hashes from CROSS-VENUE-DIAMOND-REPLICATION-002 Stage B;
- exact AVAX-USDT-SWAP instrument;
- exact funding settlement mark-price source and lower-bound adjudication path.

No spot substitution, synthetic cross rate, mark/index candle substitution for trade price, alternate quote currency, alternate venue or alternate timeframe.

## Known diagonal reconciliation baselines

These outcomes were known before this new experiment and are used only as implementation checks.

BINANCE_SIGNAL__BINANCE_EXECUTION:
- inference/resolved N = 357
- BASE funded mean = 8.550675493754708 bps
- BASE PF = 1.0477360429576321
- STRESS funded mean = 2.550675493754708 bps

OKX_SIGNAL__OKX_EXECUTION:
- inference/resolved N = 357
- BASE funded mean = 8.303857819055219 bps
- BASE PF = 1.0463580530119918
- STRESS funded mean = 2.3038578190552195 bps

Both known diagonals must reconcile within 1e-6 for means/PF and exactly on N. Otherwise:
IMPLEMENTATION_RECONCILIATION_FAIL

The known diagonal values may not be used to tune the new off-diagonal implementation.

## New outcome-blind quantities frozen now

Before execution, neither off-diagonal funded economics nor signal-concordance metrics are used to alter rules.

For every quadrant report:
- source signal count;
- resolved count;
- unresolved count;
- BASE funded mean bps;
- BASE PF;
- STRESS funded mean bps;
- positive active months / active months;
- positive quarters;
- leave-one-month-out;
- concentration ratio;
- weekly block bootstrap 95% interval.

A quadrant has FROZEN_ECONOMIC_SURVIVAL only if:
- unresolved count = 0;
- BASE mean > 0;
- BASE PF > 1;
- STRESS mean > 0;
- at least 50% of active months positive.

Bootstrap, LOMO, quarters and concentration are mandatory fragility diagnostics and cannot rescue a failed economic quadrant.

## Frozen signal concordance

Using complete inference-week source events:
- union signal days;
- intersection signal days;
- same-direction intersection;
- opposite-direction intersection;
- Binance-only signal days;
- OKX-only signal days;
- exact directional Jaccard = same-direction intersection / union signal days.

No concordance threshold is required for economic survival. It is explanatory evidence only and cannot rescue a failed quadrant.

## Overall descriptive labels

- FOUR_OF_FOUR_CROSS_EXECUTION_SURVIVAL:
  all four quadrants satisfy FROZEN_ECONOMIC_SURVIVAL and diagonal reconciliation passes.

- OFF_DIAGONALS_SURVIVE:
  both off-diagonal quadrants satisfy FROZEN_ECONOMIC_SURVIVAL and diagonal reconciliation passes.

- PARTIAL_OFF_DIAGONAL_SURVIVAL:
  exactly one off-diagonal survives.

- OFF_DIAGONAL_FAIL:
  neither off-diagonal survives.

These labels do not automatically create Tier 1, production authorization, or live-trading authority.

## Governance

research_only = true
no_live_trading = true
no_orders = true
no_exchange_mutation = true
no_authenticated_exchange_api = true
no_wallets = true
no_execution_alerts_webhooks = true
no_merge_main = true
no_2026_plus = true
no_post_outcome_tuning = true
no_venue_selection_after_outcomes = true
